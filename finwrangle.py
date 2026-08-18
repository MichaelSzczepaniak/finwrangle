import numpy as np
import pandas as pd



def convert_currency_to_float(df, col_to_convert, keep_nan=True):
    """ Converts a Pandas dataframe currency column with a str/object (string)
    dtype into float

    Args:
    df: pandas dataframe
    col_to_convert: object or str
    keep_non: bool - True (default) keeps missing values as NaNs. False converts
                     missing values to 0

    Return
    dataframe df with an updated col_to_convert column
    """
    # convert missing currency value to "0"
    if df[col_to_convert].isna().any():
        df.loc[df[col_to_convert].isna(), col_to_convert] = "0"
    
    df[col_to_convert] = df[col_to_convert].str.replace('$', "")
    df[col_to_convert] = df[col_to_convert].str.replace(',', "")
    df[col_to_convert] = df[col_to_convert].astype(float)

    if keep_nan:
        df.loc[df[col_to_convert] == 0, col_to_convert] = np.nan

    return df

def get_basis(df=None,
              amount_col='Amount',
              invert_amount=True,
              symbol_col='Symbol',
              symbol=None,
              txn_type_col='Type',
              basis_col_values=None,
              drop_cols=['Trade_date', 'Name', 'Quantity', 'Price']):
    """ Creates a dataframe with a Basis column indicating the accumulated amount
    invested in a stock or fund.
    
    Args:
        df (pandas dataframe): Dataframe holding all transactions for an account
            of interest
        amount_col (str): column name containing the values used to calculate
            basis. Default is 'Amount'
        invert_amount (bool): If True, change the sign of values in amount_col.
            Default is True
        symbol_col (str): column name in df holding the stock or fund ticker
            symbol
        symbol (str): Symbol for the stock or fund of interest (e.g. 'VMFXX')
        txn_col (str): Name of the column in df which indicates the type of
            transaction being done as described in each record (row) of df.
            Default is 'Type'
        basis_col_values (list(str)): List of strings values in the txn_col which
            need to be summed as part of the basis calculation.
        drop_cols list (list(str)): List of column names to be removed from the
            returned dataframe. Default is ['Trade_date', 'Quantity', 'Price']
    
    Returns:
        pandas dataframe:
    
    """
    # remove columns not asked for
    return_cols = [c for c in list(df.columns) if c not in drop_cols]
    if symbol is None:
        print("get_basis - NO SYMBOL SPECIFIED: RETURNING UNALTERED df")
        return df
    else:
        # filter for rows with security of interest
        df_basis = df.loc[df[symbol_col].eq(symbol), return_cols].copy()
        # filter out unneeded transactions
        df_basis = df_basis.loc[df_basis[txn_type_col].isin(basis_col_values), :].copy()
        if invert_amount:
            df_basis[amount_col] = -df_basis[amount_col]
        # calculate basis
        df_basis['Basis'] = df_basis['Amount'].cumsum()
    
    return df_basis
    
def get_position_history(df = None,
                         date_col = 'Settlement_date',
                         symbol_col = 'Symbol',
                         symbol = None,
                         quantity_col = 'Quantity',
                         price_col = 'Price',
                         txn_type_col = 'Type',
                         amount_col = 'Amount',
                         position_col_values = None,
                         div_trans_types = ['Dividend', 'Reinvestment'],
                         buy_sell_trans_types = ['Buy', 'Sell'],
                         any_div_reinvest = True,
                         buy_amount_is_negative = True,
                         drop_cols = ['Trade_date', 'Name', 'Note']):
    """ Creates a dataframe with a Units column indicating the accumulated
    position in a stock or fund.
    
    Args:
        df (pandas dataframe): Dataframe holding all transactions for an account
            of interest
        date_col (str): column name of date assigned to transaction
        symbol_col (str): column name in df holding the stock or fund ticker
            symbol
        symbol (str): Symbol for the stock or fund of interest (e.g. 'VMFXX')
        quantity_col (str): column name in df holding the number of units/shares
            that were bought or sold in a given transaction
        price_col (str): column name holding the purchase or sales price
        txn_type_col (str): Name of the column in df which indicates the type of
            transaction being done as described in each record (row) of df.
            Default is 'Type'
        amount_col (str): columns name of the amount of the purchase or sale
        position_col_values (list(str)): columns that indicate transactions that
            either increase or decrease the number of shares/units (position) of
            symbol
        div_trans_types (list(str)): values in the txn_type_col that indicate a
            dividend payment or dividend reinvestment. Default: ['Dividend',
            'Reinvestment']
        buy_sell_trans_types (list(str): values in the txn_type_col that indicate
            a sale or non-dividend purchase of shares/units. Default: ['Buy',
            'Sell']
        any_div_reinvest (bool): Are any dividends reinvested? Default is True.
        buy_amount_is_negative (bool): Are purchases represents a negative values
            in the amount column? Default is True
        drop_cols list (list(str)): List of column names to be removed from the
            returned dataframe. Default is ['Trade_date', 'Name', 'Note']
    
    Returns:
        Pandas dataframe with the position size and value of the position history
        in the 'Position' and 'Value' columns resepectively.
    
    """
    # remove columns not asked for
    return_cols = [c for c in list(df.columns) if c not in drop_cols]
    if symbol is None:
        print("get_position_history - NO SYMBOL SPECIFIED: RETURNING UNALTERED df")
        return df
    else:
        df_sym = df.loc[df[symbol_col].eq(symbol), return_cols].copy()
        # filter out unneeded transactions
        df_sym = df_sym.loc[df_sym[txn_type_col] \
                       .isin(position_col_values), :].copy()
    
    # gather the dividend-related transactions
    df_div = df_sym.loc[df_sym['Type'].isin(div_trans_types)].copy()
    # create the column identifying the paired transactions
    if any_div_reinvest:
        # The following 4 assumptions apply to any dividend reinvestment:
        #
        # assumption 1 - dividend reinvestments happen the same day the dividend
        #                is credited/received
        # assumption 2 - total dividend received = amount reinvested in new shares
        # assumption 3 - 1st of the paired transactions is the dividend received
        #                (e.g. 'Dividend')
        # assumption 4 - 2nd of the paired transactions is the dividend
        #                reinvestment (e.g. 'Reinvestment')
        df_div['paired'] = (df_div[date_col] == df_div[date_col].shift(-1)) & \
                           (df_div[amount_col] == -df_div[amount_col].shift(-1)) & \
                           (df_div[txn_type_col] == div_trans_types[0]) & \
                           (df_div[txn_type_col].shift(-1) == div_trans_types[1])
        # remove the rows that are just the div payment, keep the share purchase row
        df_div_reinvs = df_div.loc[~df_div['paired'], :].copy()
        # change the sign of the Amount col and remove the paired indicator col
        df_div_reinvs['Amount'] = -df_div_reinvs['Amount']
        df_div_reinvs.drop(['paired'], axis=1, inplace=True)
    else:
        # dividends all retained, none are reinvested
        df_div['paired'] = False
    
    # create df of sales and non-dividend purchases
    df_buy_sell = df_sym.loc[df_sym['Type'].isin(buy_sell_trans_types)].copy()
    if buy_amount_is_negative:
        df_buy_sell[amount_col] = -df_buy_sell[amount_col]
    # create df of positions
    df_positions = pd.concat([df_buy_sell, df_div_reinvs])  # axis=0 by default
    df_positions = df_positions.sort_values(by=['Settlement_date'], ascending=True)
    df_positions['Position'] = df_positions['Quantity'].cumsum()
    df_positions['Value'] = df_positions['Position'] * df_positions[price_col]
        
    return df_positions