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
            the
            to be summed as part of the basis calculation. Default is 
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
        # filter out unneeded columns
        df_basis = df_basis.loc[df_basis[txn_type_col].isin(basis_col_values), :].copy()
        if invert_amount:
            df_basis[amount_col] = -df_basis[amount_col]
        # calculate basis
        df_basis['Basis'] = df_basis['Amount'].cumsum()
    
    return df_basis