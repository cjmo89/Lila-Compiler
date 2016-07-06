import symbol_table
import sys

symboltable = symbol_table.SymbolTable(None)
    

def analyze(node):
    print "got node of type: {0}".format(node['type'])
    if node['type'] == 'translation_unit': 	return analyze_translation_unit(node)
    if node['type'] == 'assignment':		return analyze_assignment(node)
    if node['type'] == 'plus_plus': 		return analyze_shorthand_assignment(node)
    if node['type'] == 'minus_minus': 		return analyze_shorthand_assignment(node)
    if node['type'] == 'func_call':		return analyze_func_call(node)
    if node['type'] == 'func_declaration':	return analyze_function_declaration(node)

def analyze_translation_unit(node):
    for child in node['children']:
        analyze(child)

def analyze_assignment(node):
    id = node['children'][0]['children'][0]
    print "expression id = {0} at line {1}".format(id, node['lineno'])
    expression = node['children'][1]
    if(node['var_type']): 
        #this is a declaration and assignment
        #check if variable has been defined already in the current scope, lila is statically scoped and
        #does variable shadowing
        if symboltable.check_scope(id):
            print "Error at line {0}: variable {1} already defined".format(node['lineno'], id)
            sys.exit()
        #check type of expression
        type = type_check(expression)
        print "got type {0}".format(type)
        if type == node['var_type']:
            #Add symbol to symbol table
            symboltable.add_symbol(symbol_table.Symbol(id, node['var_type'], 'var', True if node['constant'] else False))
        else:
            print "Error at line {0}: variable type and expression type don't coincide".format(node['lineno'])
            sys.exit()
    else:
        #this is a simple reassignment of an existing variable
        #check if the variable has been declared
        symbol = symboltable.find_symbol(id)
        if not symbol:
            print "Error at line {0}: variable {1} does not exist".format(node['lineno'], id)
            sys.exit()
        #get type of expression being assigned
        type = type_check(expression)
        if not type == symbol.type:
            print "Error at line {0}: cannot assigned expression of type {1} to variable of type {2}".format(node['lineno'], type, symbol.type)
            sys.exit()

def analyze_shorthand_assignment(node):
    #first check if the variable being modified has been defined
    id = node['children'][0]
    symbol = symboltable.find_symbol(id)
    if not symbol:
        print "Error at line {0}: use of undefined variable {1}".format(node['lineno'], id)
        sys.exit()
    #now check if the variable is an lvalue
    if symbol.kind == 'function':
        print "Error at line {0}: cannot perform assignment to {1}, lvalue required".format(node['lineno'], id)
        sys.exit()
    #next, check if the variable is a constant
    if symbol.is_constant:
        print "Error at line {0}: cannot modify value of {1}, because it's a constan".format(node['lineno'], id)
        sys.exit()
    #now check if plusplus or minus_minusis a valid operation on this type of variable
    print symbol.type
    if symbol.type != 'integer' and symbol.type != 'real':
        print "Error at line {0}: cannot petform operation on variable of type {1}".format(node['lineno'], symbol.type)
        sys.exit()    

def analyze_func_call(node):
    #check that the function has been declared
    id = node['children'][0]['children'][0]
    print "func call id = {0}".format(id)
    symbol = symboltable.find_symbol(id)
    if not symbol:
        print "Error at line {0}: undefined function {1}".format(node['lineno'], id)
    if symbol.params:
        #check the parameters coincide with the func declaration
        if len(node['children']) < 2:
            print "Error at line {0}: function {1} requires {2} parameters, found 0".format(node['lineno'], id, len(symbol.params))
            sys.exit()
        found_params = node['children'][1]
        required_params = symbol.params
        if len(found_params) != len(required_params):
            print "Error at line {0}: function {1} requires {2} parameters, found {3}".format(node['lineno'], id, len(symbol.params), len(found_params))
            sys.exit()
        for i, param in enumerate(found_params):
            if param != required_params[i]:
                print "Error at line {0}: parameter number {1} must be of type {2}, found {3}".format(node['lineno'], i, required_params[i], param)
                sys.exit()

def analyze_function_declaration(node):
    #check the function hasn't been declared already
    id = node['children'][0]['children'][0]
    print "func declaration id = {0}".format(id)
    if symboltable.check_scope(id):
        print "Error at line {0}: function {1} already defined".format(node['lineno'], id)
        sys.exit()
    #TODO: check that the returned value coincides with the stated function type
    symboltable.add_symbol(symbol_table.Symbol(id, node['func_type'], 'function', False, node['parameters']))
    
#an expression can be either a binary op, unary op, 
#func call, parameter list, identifier or literal value
def type_check(node):
    if not isinstance(node, dict): #if node is not a dictionary then it's an explicit value
        return convert_types(type(node).__name__)
    if node['type'] == 'ID' or node['type'] == 'func_call':
        id = node['children'][0] if node['type'] == 'ID' else node['children'][0]['children'][0]
        print "func call id = {0}".format(id)
        symbol = symboltable.find_symbol(id)
        if symbol:
            return symbol.type
        else:
            obj = 'variable' if node['type'] == 'ID' else 'function'
            print "Error at line {0}: use of undefined {1} {2}".format(node['lineno'], obj, id)
            sys.exit()
    if node['type'] == 'params_list':
        parameters = []
        for param in node['children']:
            parameters.append(param['children'][0])
        return parameters
    if node['type'] == 'uminus':
        type = type_check(node['children'][0])
        if type == 'integer' or type == 'real':
            return type
        print "Error at line {0}: invalid operand type, expected integer or float, got {1}".format(node['lineno'], type)
        sys.exit()
    if node['type'] == 'not':
        type = type_check(node['children'][0])
        if type == 'boolean':
            return type
        print "Error at line {0}: invalid operand type, expected boolean, got {1}".format(node['lineno'], type)
        sys.exit()
    #type checking is done using a post-order tree traversal
    if (node['type'] == 'and' or node['type'] == 'or' or node['type'] == '>' or 
        node['type'] == '<' or node['type'] == '>=' or node['type'] == '<=' or node['type'] == 'isequals'):
        ltype = type_check(node['children'][0])
        if not ltype == 'boolean':
            print "Error at line {0}: invalid left operand type, expected boolean, got {1}".format(node['lineno'], ltype)
            sys.exit()
        rtype = type_check(node['children'][1])
        if not rtype == 'boolean':
            print "Error at line {0}: invalid right operand type, expected boolean, got {1}".format(node['lineno'], rtype)
            sys.exit()
        return 'boolean'
    if node['type'] == 'modulo':
        ltype = type_check(node['children'][0])
        if not ltype == 'integer':
            print "Error at line {0}: invalid left operand type, expected integer, got {1}".format(node['lineno'], ltype)
            sys.exit()
        rtype = type_check(node['children'][1])
        if not rtype == 'integer':
            print "Error at line {0}: invalid right operand type, expected integer, got {1}".format(node['lineno'], rtype)
            sys.exit()
        return 'integer'
    if (node['type'] == '+' or node['type'] == '-' or node['type'] == '*' or
        node['type'] == '/'):
        ltype = type_check(node['children'][0])
        if not ltype == 'integer' or not ltype == 'real':
            print "Error at line {0}: invalid left operand type, expected integer or real, got {1}".format(node['lineno'], ltype)
            sys.exit()
        rtype = type_check(node['children'][1])
        if not rtype == 'integer' or not rtype == 'real':
            print "Error at line {0}: invalid right operand type, expected integer or real, got {1}".format(node['lineno'], rtype)
            sys.exit()
        #type inference for numeric expressions:
        return 'integer' if ltype == 'integer' and rtype == 'integer' else 'real'
    print "Error: unknown type" #This error should never happen
    sys.exit()

def convert_types(type):
    switcher = {
        'int' : 'integer',
        'float' : 'real',
        'str' : 'string',
        'bool' : 'boolean'
    }
    return switcher.get(type)