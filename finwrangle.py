import numpy as np
import pandas as pd
import datetime as dt


def convert_currency_to_float(df, col_to_convert, keep_nan=True):
    """ Converts a Pandas dataframe currency column with a str/object (string)
    dtype into float

    Args:
    df: pandas dataframe
    col_to_convert: object or str - name of the column to convert to float
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
    
def fix_date_cols(df, date_col="Date", keep_first_n=10):
    """
    
    
    """
    # grab first n characters of date
    df[date_col] = df[date_col].str[:keep_first_n]
    # convert string date to datetime
    # df[date_col] = pd.to_datetime(df[date_col]).dt.date
    df[date_col] = pd.to_datetime(df[date_col])
    
    return df
    
    
    
    
def get_clean_account(df=None, config={}, unit_price_col=False):
    """ Performs the following cleaning steps to df which are described in the
    notebook: Zero out the empty values in the `Fees` column, replace spaces with
    _ in date column names, replace `NaN`s in `Symbol` column with `CASH` if value
    in `Name` columns is *CASH*, set `Price` column values to 1.00 for cash and
    money market mutual funds such as VMFXX, and replace `NaN`s in `Note` column
    with empty strings
    
    Args:
        df (pandas dataframe): Dataframe holding all transactions the entire
            account (e.g. Roth or Traditional IRA)
        config (dict): dictionary specifying key features needed to properly clean
            df. Expected keys: 'symbol_col', 'symbol_filter', 'fund_name_col',
                               'quantity_col', 'price_col', 'fees_col',
                               'amount_col', and 'notes_col'
        unit_price_col (bool): If True, sets all the values in the price_col to
            1.00 and the values in the quantity_col to the value of the Amount
            column which is useful for money market and cash accounts
    
    Returns:
      
    
    
    """
    # filter for specified account
    df_acc = df.loc[df[config['symbol_col']] == config['symbol_filter'], :].copy()
    # if share price is always $1 like money market or cash, fill in mising values
    # and set the amount = quantity
    if unit_price_col:
        df_acc.loc[df_acc[config['symbol_col']] == config['symbol_filter'],
            [config['price_col']]] = 1.00
        # for accounts with unit price: amount = quantity
        df_acc.loc[df_acc[config['symbol_col']] == config['symbol_filter'],
            [config['quantity_col']]] = df_acc[config['amount_col']]
    
    return df_acc


def get_value(df=None):
    """
    
    
    """
    
    pass




def add_basis_change(df=None,
                     config={'col_name': 'basis_change',
                             'amount_col': "Amount",
                             'type_col': "Type",
                             'basis_increase_cols': ['Sweep in', 'Reinvestment'],
                             'basis_decrease_cols': ['Sweep out', 'Dividend']}):
    """ Adds a basis_change column indicating the accumulated amount invested in a
    stock or fund.
    
    Args:
        df (pandas dataframe): Dataframe holding all transactions for a specific
            account (ticker) of interest. df must have at least columns with names
            specified by the values of config['amount_col'] and config['type_col']
        config (dict): dictionary specifying key features needed calculate basis
            Expected KVs : 'col_name' (str) - name to use for the calculated basis
                                              column,
                           'amount_col' (str) - name of column in df containing
                                                transaction amounts,
                           'type_col' (str), - name of column in df containing
                                               transaction types,
                           'basis_increase_types' list(str) - list of transaction
                                                  type which increase the basis,
                           'basis_decrease_types' list(str) - list of transaction
                                                  type which decrease the basis,
    
    Returns:
        pandas dataframe with a Basis column added
    
    """
    def basis_change(change_type, add_types, sub_types, trans_amount):
        """ Calculates the change in the investment basis for a single transaction
        
        Args:
            change_type (str): column name holding the type of transaction used to
                determine whether the amount adds to or subtracts from the basis
            add_types list(str): list of transaction types which add to the basis
            sub_types list(str): list of transaction types which subtract from the basis
            trans_amount (float): amount of the transaction impacting the basis
            
        Returns:
            float value of the change in basis for a transaction
        
        """
        if change_type in add_types:
            basis_change_val = np.abs(trans_amount)
        elif change_type in sub_types:
            basis_change_val = -np.abs(trans_amount)
        else:
            basis_change_val = float(0)
            
        return basis_change_val
    
    df_basis = df.copy()
    # if df is missing or if any of the require config keys are missing,
    # flag the user and return None
    try:
        df is not None
        try:
            required_config_keys = {'col_name', 'amount_col', 'type_col',
                                    'basis_increase_cols', 'basis_decrease_cols'}
            if len(set(config.keys()).difference(required_config_keys)) == 0:
                df_basis['basis_change'] = \
                    df_basis.apply(lambda row:
                                         basis_change(
                                             row[config['type_col']],
                                             config['basis_increase_cols'],
                                             config['basis_decrease_cols'],
                                             row[config['amount_col']]
                                         ), axis=1
                                     )
        except LookupError:
            print("add_basis function: One or more configuration keys are missing!")
            return None
    except Exception as e:
        print("basis_change: no dataframe passed in, returning None")
        df_basis = None
    
    return df_basis


def add_position_change(df = None,
                        config =
                        {
                            'col_name': 'pos_change',
                            'amount_col': "Amount",
                            'type_col': "Type",
                            'pos_increase_cols': ['Sweep in', 'Reinvestment'],
                            'pos_decrease_cols': ['Sweep out']
                        }):
    """ Adds a postion_change column indicating the accumulated shares invested in
    a stock or fund.
    
    Args:
        df (pandas dataframe): Dataframe holding all transactions for a specific
            account (ticker) of interest. df must have at least columns with names
            specified by the values of config['amount_col'] and config['type_col']
        config (dict): dictionary specifying key features needed calculate basis
            Expected KVs : 'col_name' (str) - name to use for the calculated basis
                                              column,
                           'amount_col' (str) - name of column in df containing
                                                transaction amounts,
                           'type_col' (str), - name of column in df containing
                                               transaction types,
                           'pos_increase_types' list(str) - list of transaction
                                                  type which increase the position,
                           'pos_decrease_types' list(str) - list of transaction
                                                  type which decrease the position,
    
    Returns:
        pandas dataframe with a position_change column added
    
    """
    def position_change(change_type, add_types, sub_types, trans_amount):
        """ Calculates change in the investment position for a single transaction
        
        Args:
            change_type (str): column name holding the type of transaction used to
                determine whether the amount adds to or subtracts from the position
            add_types list(str): list of transaction types which add to the position
            sub_types list(str): list of transaction types which subtract from the position
            trans_amount (float): amount of the transaction impacting the position
            
        Returns:
            float value of the change in position for a transaction
        
        """
        if change_type in add_types:
            position_change_val = np.abs(trans_amount)
        elif change_type in sub_types:
            position_change_val = -np.abs(trans_amount)
        else:
            position_change_val = float(0)
            
        return position_change_val
    # 
    df_pos = df.copy()
    # if df is missing or if any of the require config keys are missing,
    # flag the user and return None
    try:
        df is not None
        try:
            required_config_keys = {'col_name', 'amount_col', 'type_col',
                                    'pos_increase_cols', 'pos_decrease_cols'}
            if len(set(config.keys()).difference(required_config_keys)) == 0:
                df_pos['position_change'] = \
                    df_pos.apply(lambda row:
                                         position_change(
                                             row[config['type_col']],
                                             config['pos_increase_cols'],
                                             config['pos_decrease_cols'],
                                             row[config['amount_col']]
                                         ), axis=1
                                     )
        except LookupError:
            print("add_position_change: One or more configuration keys are missing!")
            return None
    except Exception as e:
        print("add_position_change: no dataframe passed in, returning None")
        df_pos = None
    
    return df_pos
    
    
    

    # calculate value based on transaction prices
    #df_positions['Value'] = df_positions['Position'] * df_positions[price_col]
    # round down in the 3rd place like Vanguard does
    #df_positions['Value'] = (np.floor(df_positions['Value'] * 100) / 100).round(2)
    
    return df_pos