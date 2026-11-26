import numpy as np
import pandas as pd
import datetime as dt
from docling.document_converter import DocumentConverter

# encapusulate Vanguard statement particulars
vanguard_statement_config = {
    'top_rows_to_skip': 3,
    'last_rows_to_skip': 6,
    'date_cols': ["Settlement date", "Trade date"],
    'drop_cols': ['Account type', 'Trade date', 'Notes'],
    'rename_cols': {
                      'Transaction type': 'Type',
                      'Commission & fees**': 'Fees',
                      'Settlement date': 'Date'
                   }
}

# encapusulate Vanguard transaction report particulars
vanguard_transactions_config = {
    'keep_cols_fixed': ['Symbol', 'Name', 'Quantity'],
    'keep_cols_prefix': ['Price on', 'Balance on']  # drop Balance on <prior month>
}

# encapusulate Schwab statement particulars ----> TODO
schwab_statement_config = {
    'top_rows_to_skip': 0,
    'last_rows_to_skip': 0,
    'date_cols': ["", ""],
    'drop_cols': ['', '', ''],
    'rename_cols': {
                      'k1': 'v1',
                      'k2': 'v2',
                      'k3': 'v3'
                   }
}

def read_txns(statement_path, statement_sheet,
              top_rows_to_skip, last_rows_to_skip,
              date_cols, drop_cols, rename_cols):
    """ Reads an investment transaction report stored in an Excel file and
    returns it as a pandas dataframe
    
    
    Args:
        statement_path
        statement_sheet
        top_rows_to_skip
        last_rows_to_skip
        date_cols
        drop_cols
        rename_cols
    
    
    Return:
    
    
    """
    df_stmt = pd.read_excel(io=statement_path,
                            sheet_name=statement_sheet,
                            skiprows = top_rows_to_skip,
                            parse_dates=date_cols,
                            skipfooter = last_rows_to_skip)
    
    df_stmt.drop(columns=drop_cols, inplace=True)
    df_stmt.rename(columns=rename_cols, inplace=True)
    
    return df_stmt


def read_vanguard_txns(
    statement_path, statement_sheet,
    top_rows_to_skip = vanguard_statement_config['top_rows_to_skip'],
    last_rows_to_skip = vanguard_statement_config['last_rows_to_skip'],
    date_cols = vanguard_statement_config['date_cols'],
    drop_cols = vanguard_statement_config['drop_cols'],
    rename_cols = vanguard_statement_config['rename_cols']):
    """ Read a Vanguard transactions report saved as an Excel file
    
    
    Args: (TODO: same as read_statement)
    
    Return: (TODO: same as read_statement)
    
    
    """
    df_vang = read_txns(statement_path, statement_sheet,
                        top_rows_to_skip, last_rows_to_skip,
                        date_cols, drop_cols, rename_cols)
    
    return df_vang


def parse_pdf_statement(statement_path, output_path):
    """ Parses a pdf investment statement and writes to a markdown file
    
    Precondition: docling package must be installed
    
    """
    converter = DocumentConverter()
    # create a docling object
    docling_obj = converter.convert(statement_path)
    # Export to markdown
    markdown_content = docling_obj.document.export_to_markdown()
    # Save to file
    with open(output_path, "w") as f:
        f.write(markdown_content)
        
    # print(f"Successfully converted {statement_path} to {output_path}")
    
    return True


def md_to_string_rows(md_file_lines=[],
                      cols_to_keep=['Symbol', 'Price on'],
                      remove_chars=['$', ',']):
    """ Converts a list of strings from a markdown file to a list of strings

    Args:
        md_file_lines list(str): list of strings where each element is a complete
        line from the markdown table

    Returns:
        list of strings that are lines of string values extracted from a markdown
        tablemd converted to csv

    """
    converted_lines = []
    
    for md_line in md_file_lines:
        converted_line = md_line.split('| ')
        # remove terminating | but specify all pipes to be sure
        converted_line[-1] = converted_line[-1].replace('|', '', count=-1)
        # remove empty first column, also makes header separator line empty - only one token!
        converted_line = converted_line[1:]
        for t, token in enumerate(converted_line):
            # remove problematic charaters from each table value
            for r in remove_chars:
                token = token.replace(r, '')
            # remove leading and trailing white space from each token
            cleaned_token = token.strip()
            converted_line[t] = cleaned_token

        # drops the md header separator line
        if len(converted_line) > 0:
            converted_lines.append(converted_line)
        
    return converted_lines


def row_lines_to_df(list_of_rows, eom_date="",
                    drop_keys=[], rename_keys={}, date_kv=("Date", ""),
                    convert_to_float=[]):
    """ Converts a list of strings that are 


    Args:
        list_of_rows: list of list(str) where each inner list holds values from a
        row in a table

    """
    # get 
    
    
    dict_of_lists = {}
    # assume first row are column headers, each corrisponding list will contain values for that column
    col_headers = list_of_rows[0]
    # print(f"column headers: {col_headers}")
    header_value_count = len(col_headers)
    dict_of_lists = {h: [] for h in col_headers}  # col names are the keys
    if len(date_kv) == 2:  # date column and the fill value
        data_row_count = len(list_of_rows) - 1
        dict_of_lists[date_kv[0]] = [date_kv[1] for i in range(data_row_count)]
        
    # check that header column count = row items
    for row in list_of_rows[1:]:  # first row are headers, start filling data
        row_value_count = len(row)
        if row_value_count != header_value_count:
            raise ValueError(f"header value count = {header_value_count} | row value count = {row_value_count}")
            sys.exit(1)
            
        for col, _ in enumerate(col_headers):
            # use index to ensure data alignment
            dict_of_lists[col_headers[col]].append(row[col])
    
    
    # drop specified columns
    if len(drop_keys) > 0:
        for drop_key in drop_keys:
            dict_of_lists.pop(drop_key)
    # rename specified columns
    if len(rename_keys) > 0:
        for old_value, new_value in rename_keys.items():
            dict_of_lists[new_value] = dict_of_lists.pop(old_value)
    #
    if len(convert_to_float) > 0:
        pass  # TODO
    
    df = pd.DataFrame(dict_of_lists)
    
    return df



def convert_currency_to_float(df, col_to_convert, keep_nan=True):
    """ Converts a Pandas dataframe currency column with a str/object (string)
    dtype into float

    Args:
        df: pandas dataframe
        col_to_convert: object or str - name of the column to convert to float
                        keep_non: bool - True (default) keeps missing values as
                        NaNs. False converts missing values to 0

    Return:
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


def sort_same_date_by(df=None, date_col='Date', by_col='Type', by_order_dict=None,
                      keep_order_col=True, by_order_asc=True):
    """ Sorts a dataframe by date_col primary and by by_col secondarily where the
    secondary sort key (by_col) order is specified by the by_order_dict.
     
    Args:
        df (pandas dataframe): Dataframe holding all transactions for a specific
            holding (e.g. VMFXX or VDIGX)
        date_col (str): name of column containing the date
        by_col (str): name of column containing the type of transaction
        by_order_dict (dict): specifies how the by_col column should be sorted.
            Keys are the unique values in the by_col column.
            Values ints specifying the order in which the secondary sort should
            be done.
    
    Returns:
        df (pandas dataframe): a cleaned Dataframe as described above
    
    """
    if (df is not None): # and (by_order_dict is not None):
        df_sorted = df.copy()
        # create custom sort order column to sort within same dates
        df_sorted['type_order'] = df_sorted[by_col].map(by_order_dict)
        if by_order_asc:
            df_sorted = df_sorted.sort_values(by=[date_col, 'type_order'],
                                              ascending=True)
        else:
            df_sorted = df_sorted.sort_values(by=[date_col, 'type_order'],
                                              ascending=False)
        if not keep_order_col:
            df_sorted.drop(columns=['type_order'], inplace=True)
    else:
        raise Exception("sort_same_date_by: Missing df, or/and by_order_dict - EXITING")

    return df_sorted


def get_clean_account(df=None, config={}, unit_price_col=False, sort_same_day={}):
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
        sort_same_day (dict):
    
    Returns:
        df (pandas dataframe): a cleaned Dataframe as described above
    
    
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
    
    if len(sort_same_day) > 0:
        df_acc = sort_same_date_by(df=df_acc,
                                   date_col=sort_same_day['date_col'],
                                   by_col=sort_same_day['by_col'],
                                   by_order_dict=sort_same_day['order_dict'],
                                   keep_order_col=sort_same_day['keep_order_col'],
                                   by_order_asc=sort_same_day['by_order_asc'])
    
    return df_acc


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
                            'quantity_col': "Quantity",
                            'type_col': "Type",
                            'pos_increase_cols': [],
                            'pos_decrease_cols': []
                        }):
    """ Adds a postion_change column indicating the accumulated shares invested in
    a stock or fund.
    
    Args:
        df (pandas dataframe): Dataframe holding all transactions for a specific
            account (ticker) of interest. df must have at least columns with names
            specified by the values of config['quantity_col'] and config['type_col']
        config (dict): dictionary specifying key features needed calculate basis
            Expected KVs : 'col_name' (str) - name to use for the calculated basis
                                              column,
                           'quantity_col' (str) - name of column in df containing
                                                  units or shares bought or sold,
                           'type_col' (str), - name of column in df containing
                                               transaction types,
                           'pos_increase_types' list(str) - list of transaction
                                                type which increase the position,
                           'pos_decrease_types' list(str) - list of transaction
                                                type which decrease the position,

    Returns:
        pandas dataframe with a position_change column added
    
    """
    def position_change(change_type, add_types, sub_types, quant_amount):
        """ Calculates change in the investment position for a single transaction
        
        Args:
            change_type (str): column name holding the type of transaction used to
                determine whether the amount adds to or subtracts from the position
            add_types list(str): list of transaction types which add to the position
            sub_types list(str): list of transaction types which subtract from the position
            quant_amount (float): number of units or shares bought or sold
            
        Returns:
            float value of the change in position for a transaction
        
        """
        if change_type in add_types:
            position_change_val = np.abs(quant_amount)
        elif change_type in sub_types:
            position_change_val = -np.abs(quant_amount)
        else:
            position_change_val = float(0)
            
        return position_change_val
    
    # if df is missing or if any of the require config keys are missing,
    # flag the user and return None
    df_pos = df.copy()
    print(f"add_position_change: shape of pass in df: {df_pos.shape}")
    try:
        required_config_keys = {'col_name', 'quantity_col', 'type_col',
                                'pos_increase_cols', 'pos_decrease_cols'}
        set_diff = set(config.keys()).difference(required_config_keys)
        if len(set_diff) == 0:
            df_pos[config['col_name']] = \
                df_pos.apply(lambda row:
                                    position_change(
                                        row[config['type_col']],
                                        config['pos_increase_cols'],
                                        config['pos_decrease_cols'],
                                        row[config['quantity_col']]
                                    ), axis=1
                             )
        else:
            print("add_position_change: config keys not the same as required")
            print(f"add_position_change - set diff: {set_diff}")
    except LookupError:
        print("add_position_change: " +
              "One or more configuration keys are missing!")
        return None
    
    if same_day_sorted:
        df_pos.reset_index(inplace=True, drop=True)
    
    return df_pos


def calc_value(df=None, config={"price_col": 'Price',
                                "position_col": 'Position',
                                "value_col": 'Value',
                                "round_down": True,
                                "round_to": 2,
                                "unit_price": False
                                }):
    """
    
    """
    
    if df is not None:
        df_value = df.copy()
    else:
        raise Exception("calc_value: No dataframe was defined. Exiting")
    
    if config["unit_price"]:
        df_value[config["value_col"]] = df_value[config["position_col"]]
    else:
        # calculate value based on transaction prices
        df_value[config["value_col"]] = df_value[config["position_col"]] * df_value[config["price_col"]]
        if config["round_down"]:
            # round down in the 3rd place like Vanguard does
            df_value[config["value_col"]] = \
                (np.floor(df_value[config["value_col"]] * 100) \
                 / 100).round(config["round_to"])
    
    return df_value


def single_row_per_statement(df, date_col='Date',
                             drop_cols=['Type', 'Quantity', '']):
    
    pass