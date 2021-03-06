# -----------------------------------------------------------------------------
# mojo_parser.py
#
# A simple parser for the mojo language.
# -----------------------------------------------------------------------------

### LIST OF ACTIONS ###
# Embedded actions not part of the syntax
# cfd_action -> Create function directory
# adv_action -> Add a variable to the current function
# ada_action -> Adds a dimensioned variable to the current function
# adf_action -> Adds a new function to the directory
# amf_action -> Adds the main function to the directory
# pio_action -> Push a variable operand to the stack
# pfo_action -> Push float operand to the stack
# pso_action -> Push string operand to the stack
# pbo_action -> Push boolean operand to the stack
# pid_action -> Push id operand to stack
# pop_action -> Push an operator to its stack
# sot_action -> Solve term
# sof_action -> Solve factor
# sor_action -> Solve relational operations
# sol_action -> Solve logical operations
# soa_action -> Solve assignment
# abm_action -> Add bottom mark
# rbm_action -> Remove bottom mark
# cif_action -> Create if conditional quadruple
# sif_action -> Solve if conditional quadruple
# cel_action -> Create else quadruple
# cwl_action -> Creates the while quadruple
# cwr_action -> Creates the write quadruple
# swl_action -> Solves the while quadruple
# enp_action -> Ends the procedure closing with a quadruple and solve returns
# cra_action -> Creates de era quadruple action
# sar_action -> Solve argument
# sfc_action -> Solve function call
# srf_action -> Sets on the return flag and creates its quadruples
# vtc_action -> Verifies the type of the procedure call
# arf_action -> Adds the result of the function to the stack
# ivd_action -> Identifies the dimensions of a variable when declared
# idv_action -> Identifies the dimensioned variable called
# cdv_action -> Calls the dimensional variable verifications and resolves it
# tnf_action -> Turns on the negation flag
# snc_action -> Solves the negation call
# vcv_action -> Verifies that variable is of type string

### LIST OF PREDEFINED FUNCTIONS ###
# Functions proper of the application of the language
# pfc_create_turtle  -> Creates a new instance of a turtle object
# pfc_reset          -> Erases the current turtle's drawings and resets the turtle at the starting point
# pfc_finish_drawing -> Stops the graphical output window
# pfc_pen_up         -> The turtle stops drawing when moved
# pfc_pen_down       -> The turtle draws when moved
# pfc_begin_fill     -> Indicates that next drawings will be filled with fillcolor
# pfc_end_fill       -> Previous drawings are filled with the current fillcolor
# pfc_pen_color      -> Sets the current color of the pen
# pfc_fill_color     -> Sets the current color of the filling
# pfc_pen_width      -> Sets the width size of the pen
# pfc_move_forward   -> Moves the turtle a certain distance forward
# pfc_move_right     -> Moves the turtle a certain distance to the right(90 degrees) #
# pfc_move_left      -> Moves the turtle a certain distance to the left(-90 degrees)
# pfc_turn_right     -> Turns the turtle certain degrees to the right
# pfc_turn_left      -> Turns the turtle certain degrees to the left
# pfc_draw_square    -> Draws a square
# pfc_draw_triangle  -> Draws an equilateral triangle
# pfc_draw_circle    -> Draws a circle of a certain radius length
# pfc_draw_rectangle -> Draws a rectangle with a certain upper and bottom side length and a certain left and right side length
# pfc_set_position   -> Set the turtle in the position received

import sys
import ply.yacc as yacc

from mojo_lexer import tokens
from helpers.program import Program
from helpers.quadruple import Quadruple
from helpers.virtual_machine import VirtualMachine

my_program = Program()

# Parsing rules
def p_program(p):
    '''program : PROGRAM ID cmq_action cfd_action SEMICOLON vars functions MAIN amf_action block'''
    print('Syntax correct')

# Creates the main quadruple GoTo action
def p_cmq_action(p):
    '''cmq_action : '''
    quadruple = Quadruple(my_program.quadruple_number, 'GOTO', 'MAIN', None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

# Creates the function directory
def p_cfd_action(p):
    '''cfd_action : '''
    my_program.global_scope = p[-2]
    my_program.current_scope = p[-2]

    # Adds the program, the global scope, to the directory
    my_program.function_directory.add_function(my_program.global_scope, 'void')

def p_vars(p):
    '''vars : VAR ID more_vars COLON type adv_action SEMICOLON vars
            | VAR ID list_declaration COLON type ada_action SEMICOLON vars
            | empty'''

def p_list_declaration(p):
    '''list_declaration : LBRACKET var_const RBRACKET ivd_action'''

# Identifies the dimensions of a variable when declared
def p_ivd_action(p):
    '''ivd_action : '''
    dimensioned_varible_name = p[-4]
    dimension_size_address = my_program.operand_stack.pop()
    dimension_size = my_program.memory.get_value(dimension_size_address)
    dimension_type = my_program.type_stack.pop()

    # Verifies the dimension of the variable
    if dimension_type != 'int':
        print("Array indexes should be of type int")
        sys.exit()
    elif dimension_size < 1:
        print("Array dimension should be greater than 0")
        sys.exit()
    else:
        # Adds the information of the variable
        my_program.dimensioned_varible_flag = True
        my_program.current_dimensioned_varible = {
            'name' : dimensioned_varible_name,
            'lower_limit' : 0,
            'upper_limit' : dimension_size,
        }

def p_more_vars(p):
    '''more_vars : COMMA ID more_vars
                 | empty'''
    # Stores the variables found in a temporal list
    if p[-1] is not None:
        variable_name = p[-1]
        my_program.temporal_variables.append(variable_name)

# Adds a variable to the current function
def p_adv_action(p):
    '''adv_action : '''
    variable_type = p[-1]
    my_program.temporal_variables.reverse()

    # Adds all the variables declared in the line to the function
    for variable in my_program.temporal_variables:
        variable_declared = my_program.function_directory.check_existing_variable(
            my_program.current_scope, variable)

        if not variable_declared:
            # Request the addresses depending of the scope
            if my_program.current_scope == my_program.global_scope:
                variable_address = my_program.memory.request_global_address(variable_type)
            else:
                variable_address = my_program.memory.request_local_address(variable_type)

            my_program.function_directory.add_variable_to_function(
                my_program.current_scope, variable_type, variable, variable_address)

    # Clears the list of temporal variables to start a new line of declarations
    del my_program.temporal_variables[:]

# Adds a dimensioned variable to the current function
def p_ada_action(p):
    '''ada_action : '''
    variable_type = p[-1]
    variable = my_program.current_dimensioned_varible
    variable_declared = my_program.function_directory.check_existing_variable(
        my_program.current_scope, variable['name'])

    if not variable_declared:
        # Request the addresses needed for the variable
        if my_program.current_scope == my_program.global_scope:
            variable_address = my_program.memory.request_sequential_global_addresses(
                variable_type, variable['upper_limit'])
        else:
            variable_address = my_program.memory.request_sequential_local_addresses(
                variable_type, variable['upper_limit'])

        variable['type'] = variable_type
        variable['memory_adress'] = variable_address

        my_program.function_directory.add_dimensioned_variable_to_function(
            my_program.current_scope, variable)

def p_functions(p):
    '''functions : DEF function_type ID LPAREN parameters RPAREN adf_action block enp_action functions
                 | empty'''

def p_function_type(p):
    '''function_type : type
                     | VOID'''
    p[0] = p[1]

def p_parameters(p):
    '''parameters : type ID more_parameters
                  | empty'''

def p_more_parameters(p):
    '''more_parameters : COMMA type ID more_parameters
                       | empty'''
    # Stores the types parameters found in the temporal list, parameters
    # are found from the last one to the first one, they need to be inserted
    # in the first index to keep the order
    if p[-1] is not None:
        parameter_name = p[-1]
        parameter_type = p[-2]
        my_program.temporal_parameters_names.insert(0, parameter_name)
        my_program.temporal_parameters_types.insert(0, parameter_type)

def p_type(p):
    '''type : INT
            | FLOAT
            | STRING
            | BOOLEAN'''
    p[0] = p[1]

# Adds a new function and its parameters to the directory
def p_adf_action(p):
    '''adf_action : '''
    ### 1. Need to separate space in the global memory for the return value if its
    ### not a void function, the whole function acts like a variable in te global memory
    ### 2. Validate the te funcion hasn't been declared yet

    # Determines the name of the function and its type
    my_program.current_scope = p[-4]
    function_type = p[-5]
    parameter_adresses_list = []

    # Adds the function to the directory
    my_program.function_directory.add_function(my_program.current_scope, function_type)

    # Sets the starting quadruple of the function
    my_program.function_directory.set_function_quadruple_number(my_program.current_scope,
        my_program.quadruple_number)

    if function_type != 'void':
        # Sets the address return of the function
        function_address = my_program.memory.request_global_address(function_type)
        my_program.function_directory.set_function_address(my_program.current_scope,
            function_address)

    # Adds the parameters to the function variable table
    parameters = zip(my_program.temporal_parameters_names,
        my_program.temporal_parameters_types)

    for parameter_name, parameter_type in parameters:
        parameter_adress = my_program.memory.request_local_address(parameter_type)
        parameter_adresses_list.append(parameter_adress)
        my_program.function_directory.add_variable_to_function(
                my_program.current_scope, parameter_type, parameter_name, parameter_adress)

    # Adds the parameters signature to the function
    my_program.function_directory.add_parameter_to_function(my_program.current_scope,
            list(my_program.temporal_parameters_types), list(parameter_adresses_list))

    # Clears the temporal parameters
    del my_program.temporal_parameters_names[:]
    del my_program.temporal_parameters_types[:]

# Creates the quadruple that indicates the end of the procedure
def p_enp_action(p):
    '''enp_action : '''
    function_type = p[-7]

    # Checks if the functions and procedures have the correct return semantics
    if function_type == 'void' and my_program.return_flag:
        print('Function {0} of type {1} should not have return statement.'.format(
            my_program.current_scope, function_type))
        sys.exit()
    elif function_type != 'void' and not my_program.return_flag:
        print('Function {0} of type {1} should have return statement.'.format(
            my_program.current_scope, function_type))
        sys.exit()
    else:
        # Creates the end of function quadruple
        quadruple = Quadruple(my_program.quadruple_number, 'ENDPROC', None, None, None)
        my_program.quadruple_list.append(quadruple)

    # Fills the returns quadruples if exist
    if my_program.return_flag:
        while my_program.return_list:
            quadruple_number_to_fill = my_program.return_list.pop()
            my_program.quadruple_list[quadruple_number_to_fill - 1].fill_quadruple_jump(
                my_program.quadruple_number)

    my_program.quadruple_number += 1
    my_program.return_flag = False

    # Reset the temporal memory
    my_program.current_scope = my_program.global_scope
    my_program.memory.reset_temporal_memory()

# Adds the main function to function directory
def p_amf_action(p):
    '''amf_action : '''
    my_program.current_scope = p[-1]
    my_program.function_directory.add_function(my_program.current_scope, 'void')
    my_program.function_directory.set_function_quadruple_number(my_program.current_scope,
        my_program.quadruple_number)

    # Fills the quadruple jump number of the program to the main function
    quadruple = my_program.quadruple_list[0]
    quadruple.fill_quadruple_jump(my_program.quadruple_number)

def p_block(p):
    '''block : LBRACE statements RBRACE'''

def p_statements(p):
    '''statements : vars statement statements
                  | vars empty'''

def p_statement(p):
    '''statement : assignment
                 | condition
                 | write
                 | loop
                 | procedure_call
                 | predefined_function_call
                 | return '''

def p_assignment(p):
    '''assignment : ID pid_action list_call ASSIGN pop_action super_expression SEMICOLON soa_action
                  | ID pid_action list_call ASSIGN pop_action READ LPAREN super_expression RPAREN crq_action SEMICOLON soa_action'''

# Creates the read quadruple
def p_crq_action(p):
    '''crq_action : '''
    message_address = my_program.operand_stack.pop()
    my_program.type_stack.pop()

    # Gets the type of the variable where the input will be stored and request
    # a temporal address to resolve its assignment
    variable_type = my_program.type_stack[-1]
    input_address = my_program.memory.request_temporal_address(variable_type)

    my_program.operand_stack.append(input_address)
    my_program.type_stack.append(variable_type)

    quadruple = Quadruple(my_program.quadruple_number, 'READ', variable_type,
        message_address, input_address)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_list_call(p):
    '''list_call : LBRACKET idv_action abm_action exp cdv_action rbm_action RBRACKET
                       | empty'''

# Identifies a dimensioned variable when called
def p_idv_action(p):
    '''idv_action : '''
    variable_name = p[-3]
    my_program.operand_stack.pop()

    # Checks if the variable exists in the local scope
    variable = my_program.function_directory.get_function_variable(
        my_program.current_scope, variable_name)

    if variable is None:
        # Checks if the variable exists in the global scope
        variable = my_program.function_directory.get_function_variable(
            my_program.global_scope, variable_name)
        if variable is None:
            print("The variable " + variable_name + " has not been declared")
            sys.exit()
        else:
            if 'upper_limit' in variable:
                # Appends the dimensioned variable to a stack, makes nesting
                # vectors calls possible
                my_program.dimensioned_varible_stack.append(variable)
            else:
                print("The variable " + variable_name + " is not an array")
                sys.exit()
    else:
        if 'upper_limit' in variable:
            # Appends the dimensioned variable to a stack, makes nesting
            # vectors calls possible
            my_program.dimensioned_varible_stack.append(variable)
        else:
            print("The variable " + variable_name + " is not an array")
            sys.exit()

# Verifies the boundaries of the dimensioned variable and resolves its index
def p_cdv_action(p):
    '''cdv_action : '''
    index_address = my_program.operand_stack.pop()
    index_type = my_program.type_stack.pop()

    # Returns the last dimensioned variable called
    dimensioned_variable = my_program.dimensioned_varible_stack.pop()

    # Verifies the type of the index
    if index_type != 'int':
        print("Array indexes should be of type int")
        sys.exit()
    else:
        # Verifies the boundaries
        quadruple = Quadruple(my_program.quadruple_number, 'VERF_INDEX',
            index_address, dimensioned_variable['lower_limit'], dimensioned_variable['upper_limit'])
        my_program.quadruple_list.append(quadruple)
        my_program.quadruple_number += 1

        # The base address of the dimensioned variable must be stored in new
        # address, this makes possible the adding of the base address number and
        # not its content
        base_address_proxy = my_program.memory.request_global_address('int',
            dimensioned_variable['memory_adress'])
        index_address_result = my_program.memory.request_global_address('int')

        # Adds the base address number with the result of the index
        quadruple = Quadruple(my_program.quadruple_number, '+', base_address_proxy,
            index_address, index_address_result)
        my_program.quadruple_list.append(quadruple)
        my_program.quadruple_number += 1

        # Stores the index address result int a dictionary to difference it
        # from a regular address
        result_proxy = {'index_address' : index_address_result}
        my_program.operand_stack.append(result_proxy)
        my_program.type_stack.append(dimensioned_variable['type'])

# Solves the assignment and creates its quadruple
def p_soa_action(p):
    '''soa_action : '''
    # Gets the operator
    operator = my_program.operator_stack.pop()

    if operator == '=':
        # Gets the operands and its types
        right_operand = my_program.operand_stack.pop()
        right_type = my_program.type_stack.pop()
        left_operand = my_program.operand_stack.pop()
        left_type = my_program.type_stack.pop()

        # Gets the type of the result
        result_type = my_program.semantic_cube.get_semantic_type(left_type ,
            right_type, operator)

        if result_type != 'error':
            # Creates the quadruple
            quadruple = Quadruple(my_program.quadruple_number, operator,
                right_operand, None , left_operand)

            # Adds the quadruple to its list and increments the counter
            my_program.quadruple_list.append(quadruple)
            my_program.quadruple_number += 1
        else:
            print('Operation type mismatch at {0}'.format(p.lexer.lineno))
            sys.exit()

def p_condition(p):
    '''condition : IF LPAREN super_expression RPAREN cif_action block else sif_action'''

# Create if conditional quadruple action
def p_cif_action(p):
    '''cif_action : '''
    create_conditional_quadruple(p)

def p_else(p):
    '''else : ELSE cel_action block
            | empty'''

# Create else quadruple
def p_cel_action(p):
    '''cel_action : '''
    # Creates the GoTo quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'GOTO', None, None, None)
    my_program.quadruple_list.append(quadruple)

    # Gets the number of the GotoF quadruple to be filled
    quadruple_number_to_fill = my_program.jump_list.pop()
    quadruple = my_program.quadruple_list[quadruple_number_to_fill]

    # Stores the actual quadruple_number GoTo in the jump list
    my_program.jump_list.append(my_program.quadruple_number - 1)
    my_program.quadruple_number += 1

    # Fills the pending GoToF quadruple with the number of the next quadruple
    # after GoTo was created
    quadruple.fill_quadruple_jump(my_program.quadruple_number)

# Fills the pending GoToF quadruples
def p_sif_action(p):
    '''sif_action : '''
    # Gets the number of the GotoF quadruple to be filled
    quadruple_number_to_fill = my_program.jump_list.pop()
    quadruple = my_program.quadruple_list[quadruple_number_to_fill]

    # Fills the pending GoToF quadruple with the number of the next quadruple
    quadruple.fill_quadruple_jump(my_program.quadruple_number)

def p_super_expression(p):
    '''super_expression : negation expression sol_action
                        | negation expression sol_action AND pop_action super_expression
                        | negation expression sol_action OR pop_action super_expression'''

# Solve logical operations
def p_sol_action(p):
    '''sol_action : '''
    if len(my_program.operator_stack) > 0 and len(my_program.operand_stack) > 1:
        if my_program.operator_stack[-1] == 'and' or my_program.operator_stack[-1] == 'or':
            solve_operation(p)

def p_negation(p):
    '''negation : NOT
                | empty'''

# def p_snc_action(p):
#     '''snc_action : '''
#     if my_program.negation_stack[-1]:
#         my_program.negation_stack.pop()
#         left_operand = my_program.operand_stack[-1]
#
#         quadruple = Quadruple(my_program.quadruple_number, 'NOT', left_operand,
#             None, left_operand)
#         my_program.quadruple_list.append(quadruple)
#         my_program.quadruple_number += 1
#
# # Turns on the negation flag
# def p_tnf_action(p):
#     '''tnf_action : '''
#     my_program.negation_stack.append(True)

def p_expression(p):
    '''expression : exp sor_action
                  | exp GT pop_action exp sor_action
                  | exp LT pop_action exp sor_action
                  | exp LE pop_action exp sor_action
                  | exp GE pop_action exp sor_action
                  | exp EQ pop_action exp sor_action
                  | exp NE pop_action exp sor_action'''

# Solve relational operations
def p_sor_action(p):
    '''sor_action : '''
    if len(my_program.operator_stack) > 0 and len(my_program.operand_stack) > 1:
        if my_program.operator_stack[-1] in my_program.relational_operations:
            solve_operation(p)

def p_exp(p):
    '''exp : term sot_action
           | term sot_action PLUS pop_action exp
           | term sot_action MINUS pop_action exp '''

# Solve term
def p_sot_action(p):
    '''sot_action : '''
    if len(my_program.operator_stack) > 0 and len(my_program.operand_stack) > 1:
        if my_program.operator_stack[-1] == '+' or my_program.operator_stack[-1] == '-':
            solve_operation(p)

def p_term(p):
    '''term : factor sof_action
            | factor sof_action TIMES pop_action term
            | factor sof_action DIVIDE pop_action term'''

# Solve factor
def p_sof_action(p):
    '''sof_action : '''
    if len(my_program.operator_stack) > 0 and len(my_program.operand_stack) > 1:
        if my_program.operator_stack[-1] == '*' or my_program.operator_stack[-1] == '/':
            solve_operation(p)

def p_factor(p):
    '''factor : LPAREN abm_action super_expression RPAREN rbm_action
              | var_const '''

# Adds a false bottom mark to the operator stack
def p_abm_action(p):
    '''abm_action : '''
    my_program.operator_stack.append('()')

# Removes the false bottom mark
def p_rbm_action(p):
    '''rbm_action : '''
    my_program.operator_stack.pop()

# Push an operator to its stack
def p_pop_action(p):
    '''pop_action : '''
    my_program.operator_stack.append(p[-1])

def p_var_const(p):
    '''var_const : ID pid_action list_call
                 | ICONST pio_action
                 | FCONST pfo_action
                 | SCONST pso_action
                 | boolean_value pbo_action
                 | function_call'''

# Push a variable to the operand stack
def p_pid_action(p):
    '''pid_action : '''
    # Checks if the variable exists in the local scope
    # print("Scope : " + my_program.current_scope)
    variable = my_program.function_directory.get_function_variable(
        my_program.current_scope, p[-1])

    if variable is None:
        # Checks if the variable exists in the global scope
        # print("Scope : " + my_program.global_scope)
        variable = my_program.function_directory.get_function_variable(
            my_program.global_scope, p[-1])
        if variable is None:
            print("The variable " + p[-1] + " has not been declared")
            sys.exit()
        else:
            # Adds the variale to the operand stack
            my_program.operand_stack.append(variable['memory_adress'])
            my_program.type_stack.append(variable['type'])
    else:
        # Adds the variale to the operand stack
        my_program.operand_stack.append(variable['memory_adress'])
        my_program.type_stack.append(variable['type'])

# Push an intenger to the operand stack
def p_pio_action(p):
    '''pio_action : '''
    # Gets the constant address, creates one if doesn't exists
    constant_address = my_program.memory.check_existing_constant_value('int', int(p[-1]))
    if constant_address is None:
        constant_address = my_program.memory.request_constant_address('int', int(p[-1]))

    my_program.operand_stack.append(constant_address)
    my_program.type_stack.append('int')

# Push a float to the operand stack
def p_pfo_action(p):
    '''pfo_action : '''
    # Gets the constant address, creates one if doesn't exists
    constant_address = my_program.memory.check_existing_constant_value('float', float(p[-1]))
    if constant_address is None:
        constant_address = my_program.memory.request_constant_address('float', float(p[-1]))

    my_program.operand_stack.append(constant_address)
    my_program.type_stack.append('float')

# Push a string to the operand stack
def p_pso_action(p):
    '''pso_action : '''
    # Gets the constant address, creates one if doesn't exists
    constant_address = my_program.memory.check_existing_constant_value('string', str(p[-1]))
    if constant_address is None:
        constant_address = my_program.memory.request_constant_address('string', str(p[-1]))

    my_program.operand_stack.append(constant_address)
    my_program.type_stack.append('string')

# Push a boolean to the operand stack
def p_pbo_action(p):
    '''pbo_action : '''
    if p[-1] == "True":
        # Gets the constant address, creates one if doesn't exists
        constant_address = my_program.memory.check_existing_constant_value('bool', True)
        if constant_address is None:
            constant_address = my_program.memory.request_constant_address('bool', True)

        my_program.operand_stack.append(constant_address)
        my_program.type_stack.append('bool')
    else:
        # Gets the constant address, creates one if doesn't exists
        constant_address = my_program.memory.check_existing_constant_value('bool', False)
        if constant_address is None:
            constant_address = my_program.memory.request_constant_address('bool', False)

        my_program.operand_stack.append(constant_address)
        my_program.type_stack.append('bool')

def p_boolean_value(p):
    '''boolean_value : TRUE
                     | FALSE'''
    p[0] = p[1]

def p_loop(p):
    '''loop : WHILE cwl_action LPAREN super_expression RPAREN cif_action block swl_action'''

# Stores the actual quaduple number to be used later for the while
def p_cwl_action(p):
    '''cwl_action : '''
    my_program.jump_list.append(my_program.quadruple_number)

def p_swl_action(p):
    '''swl_action : '''
    # Gets the number of the GotoF quadruple and where the while starts
    quadruple_number_to_fill = my_program.jump_list.pop()
    quadruple_number_to_return = my_program.jump_list.pop()

    while_quadruple = Quadruple(my_program.quadruple_number, 'GOTO', None, None,
        quadruple_number_to_return)

    my_program.quadruple_list.append(while_quadruple)
    my_program.quadruple_number += 1

    conditional_quadruple = my_program.quadruple_list[quadruple_number_to_fill]
    # Fills the pending GoToF quadruple with the number of the next quadruple
    conditional_quadruple.fill_quadruple_jump(my_program.quadruple_number)

def p_procedure_call(p):
    '''procedure_call : ID LPAREN abm_action cra_action arguments RPAREN rbm_action sfc_action vtc_action SEMICOLON'''

def p_function_call(p):
    '''function_call : ID LPAREN abm_action cra_action arguments RPAREN rbm_action sfc_action arf_action'''

# Verifies if the procedure call is void type
def p_vtc_action(p):
    '''vtc_action : '''
    function = p[-8]
    function_type = my_program.function_directory.get_function_type(function)

    if function_type != 'void':
        print("This function {0} can't be called as a procedure".format(function))
        sys.exit()

# Checks if the function directory has the function called and creates its
# ERA action
def p_cra_action(p):
    '''cra_action : '''
    function = p[-3]
    # Checks if the function exists
    if my_program.function_directory.has_function(function):
        # Creates its quadruple action
        quadruple = Quadruple(my_program.quadruple_number, 'ERA', function, None, None)
        my_program.quadruple_list.append(quadruple)
        my_program.quadruple_number += 1

        # Retrieves the parameters of the function
        parameters = my_program.function_directory.get_function_parameters(function)
        my_program.temporal_arguments_types = list(parameters['types'])
    else:
        print("The function " + function + " you are trying to call doesn't exists")
        sys.exit()

def p_arguments(p):
    '''arguments : super_expression sar_action more_arguments
                 | empty'''

def p_more_arguments(p):
    '''more_arguments : COMMA super_expression sar_action more_arguments
                      | empty'''

# Solve argument
def p_sar_action(p):
    '''sar_action : '''
    # If there are more arguments than parameters
    if my_program.temporal_arguments_types:
        # Gets the argument and its type from the stacks
        argument = my_program.operand_stack.pop()
        argument_type = my_program.type_stack.pop()
        parameter_type = my_program.temporal_arguments_types.pop(0)

        # Creates the quadruple for the parameter
        if argument_type == parameter_type:
            quadruple = Quadruple(my_program.quadruple_number, 'PARAMETER', argument,
                None, None)
            my_program.quadruple_list.append(quadruple)
            my_program.quadruple_number += 1
        else:
            print('Argument type mismatch at {0} line '.format(p.lexer.lineno))
            sys.exit()
    else:
        print('Agument number mismatch at {0} line '.format(p.lexer.lineno))
        sys.exit()

# Solves the function-procedure called
def p_sfc_action(p):
    '''sfc_action : '''
    # If there are more parameters than arguments
    if not my_program.temporal_arguments_types:
        # Retrieves the function and is quadruple number
        function = p[-7]
        function_quadruple_number = my_program.function_directory.get_function_quadruple_number(function)

        # Creates its call quadruple
        quadruple = Quadruple(my_program.quadruple_number, 'GOSUB', function,
            None, function_quadruple_number)
        my_program.quadruple_list.append(quadruple)
        my_program.quadruple_number += 1
    else:
        print('Argument number mismatch at {0} line '.format(p.lexer.lineno))
        sys.exit()

# Adds the result of the function to the stack and creates its quadruple
def p_arf_action(p):
    '''arf_action : '''
    function_called = p[-8]
    function = my_program.function_directory.get_function(function_called)
    function_return = function['return_address']
    function_type = function['return_type']

    #my_program.temporal_variable_counter += 1

    # Requests a temporal variable to store the result of the function
    temporal_variable_address = my_program.memory.request_temporal_address(function_type)
    my_program.function_directory.add_temporal_to_function(my_program.current_scope,
        function_type)

    # Assignates the result to a new temporal variable and adds it to the
    # operand stack
    quadruple = Quadruple(my_program.quadruple_number, '=', function_return, None,
        temporal_variable_address)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

    my_program.operand_stack.append(temporal_variable_address)
    my_program.type_stack.append(function_type)

def p_predefined_function_call(p):
    '''predefined_function_call : CREATE_TURTLE LPAREN RPAREN pfc_create_turtle SEMICOLON
                                | RESET LPAREN RPAREN pfc_reset SEMICOLON
                                | FINISH_DRAWING LPAREN RPAREN pfc_finish_drawing SEMICOLON
                                | PEN_UP LPAREN RPAREN  pfc_pen_up SEMICOLON
                                | PEN_DOWN LPAREN RPAREN pfc_pen_down SEMICOLON
                                | BEGIN_FILL LPAREN RPAREN pfc_begin_fill SEMICOLON
                                | END_FILL LPAREN RPAREN pfc_end_fill SEMICOLON
                                | PEN_COLOR LPAREN var_string RPAREN pfc_pen_color SEMICOLON
                                | FILL_COLOR LPAREN var_string RPAREN pfc_fill_color SEMICOLON
                                | PEN_WIDTH LPAREN exp RPAREN pfc_pen_width SEMICOLON
                                | MOVE_FORWARD LPAREN exp RPAREN pfc_move_forward SEMICOLON
                                | MOVE_RIGHT LPAREN exp RPAREN pfc_move_right SEMICOLON
                                | MOVE_LEFT LPAREN exp RPAREN pfc_move_left SEMICOLON
                                | TURN_RIGHT LPAREN exp RPAREN pfc_turn_right SEMICOLON
                                | TURN_LEFT LPAREN exp RPAREN pfc_turn_left SEMICOLON
                                | DRAW_SQUARE LPAREN exp RPAREN pfc_draw_square SEMICOLON
                                | DRAW_TRIANGLE LPAREN exp RPAREN pfc_draw_triangle SEMICOLON
                                | DRAW_CIRCLE LPAREN exp RPAREN pfc_draw_circle SEMICOLON
                                | DRAW_RECTANGLE LPAREN exp COMMA exp RPAREN pfc_draw_rectangle SEMICOLON
                                | SET_POSITION LPAREN exp COMMA exp RPAREN pfc_set_position SEMICOLON
                                | SET_SPEED LPAREN exp RPAREN pfc_set_speed SEMICOLON'''

def p_return(p):
    '''return : RETURN super_expression SEMICOLON srf_action'''

# Sets on the return flag and creates the return quadruples
def p_srf_action(p):
    '''srf_action : '''
    my_program.return_flag = True

    # Gets the return operand and the function been called
    operand = my_program.operand_stack.pop()
    operand_type = my_program.type_stack.pop()
    function = my_program.function_directory.get_function(my_program.current_scope)
    function_type = function['return_type']
    function_return_address = function['return_address']

    # Checks if the types match
    if function_type != operand_type:
        print("Return type of function {0} doesn't match function return type".format(
            my_program.current_scope))
        sys.exit()

    # Creates the returns quadruples and sets the adress they will return
    quadruple = Quadruple(my_program.quadruple_number, 'RETURN', operand, None,
        function_return_address)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

    # Creates the GOTO quadruple and stores them in a stack for multiple returns
    quadruple = Quadruple(my_program.quadruple_number, 'GOTO', None, None, None)
    my_program.return_list.append(my_program.quadruple_number)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_write(p):
    '''write : PRINT LPAREN super_expression cwr_action RPAREN SEMICOLON'''

# Creates the write quadruple
def p_cwr_action(p):
    '''cwr_action : '''
    operand = my_program.operand_stack.pop()

    quadruple = Quadruple(my_program.quadruple_number, 'PRINT', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_empty(p):
    '''empty : '''

def p_error(p):
    print('Syntax error at input line {0}'.format(p.lexer.lineno))
    sys.exit()

# START OF PREDEFINED FUNCTIONS
def p_pfc_create_turtle(p):
    '''pfc_create_turtle : '''
    # Creates the CREATE_TURTLE quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'CREATE_TURTLE', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_reset(p):
    '''pfc_reset : '''
    # Creates the RESET quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'RESET', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_finish_drawing(p):
    '''pfc_finish_drawing : '''
    # Creates the FINISH_DRAWING quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'FINISH_DRAWING', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_pen_up(p):
    '''pfc_pen_up : '''
    # Creates the PEN_UP quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'PEN_UP', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_pen_down(p):
    '''pfc_pen_down : '''
    # Creates the PEN_DOWN quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'PEN_DOWN', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_begin_fill(p):
    '''pfc_begin_fill : '''
    # Creates the BEGIN_FILL quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'BEGIN_FILL', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_end_fill(p):
    '''pfc_end_fill : '''
    # Creates the END_FILL quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'END_FILL', None, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_pen_color(p):
    '''pfc_pen_color : '''
    # Gets the color (string constant) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the PEN_COLOR quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'PEN_COLOR', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_fill_color(p):
    '''pfc_fill_color : '''
    # Gets the color (string constant) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the PEN_COLOR quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'FILL_COLOR', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_pen_width(p):
    '''pfc_pen_width : '''
    # Gets the width size number (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the PEN_WIDTH quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'PEN_WIDTH', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_move_forward(p):
    '''pfc_move_forward : '''
    # Gets the distance number (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the MOVE_FORWARD quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'MOVE_FORWARD', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_move_right(p):
    '''pfc_move_right : '''
    # Gets the distance number (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the MOVE_RIGHT quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'MOVE_RIGHT', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_move_left(p):
    '''pfc_move_left : '''
    # Gets the distance number (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the MOVE_LEFT quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'MOVE_LEFT', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_turn_right(p):
    '''pfc_turn_right : '''
    # Gets the degrees number (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the TURN_RIGHT quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'TURN_RIGHT', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_turn_left(p):
    '''pfc_turn_left : '''
    # Gets the degrees number (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the TURN_LEFT quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'TURN_LEFT', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_draw_square(p):
    '''pfc_draw_square : '''
    # Gets the length of the sides of the square (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the DRAW_SQUARE quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'DRAW_SQUARE', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_draw_triangle(p):
    '''pfc_draw_triangle : '''
    # Gets the length of the sides of the triangle (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the DRAW_TRIANGLE quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'DRAW_TRIANGLE', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_draw_circle(p):
    '''pfc_draw_circle : '''
    # Gets the length of the radius of the circle (exp) from the operand stack
    operand = my_program.operand_stack.pop()
    # Creates the DRAW_CIRCLE quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'DRAW_CIRCLE', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_draw_rectangle(p):
    '''pfc_draw_rectangle : '''
    # Gets the length of the left and right sides of the rectangle (exp) from the operand stack
    height = my_program.operand_stack.pop()
    # Gets the length of the upper and bottom sides of the rectangle (exp) from the operand stack
    width = my_program.operand_stack.pop()
    # Creates the DRAW_RECTANGLE quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'DRAW_RECTANGLE', width, height, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_set_position(p):
    '''pfc_set_position : '''
    # Gets the position on X axis
    y_axis = my_program.operand_stack.pop()
    # Gets the position on Y axis
    x_axis = my_program.operand_stack.pop()
    # Creates the SET_POSITION quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'SET_POSITION', x_axis, y_axis, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

def p_pfc_set_speed(p):
    '''pfc_set_speed : '''
    # Gets the speed number
    operand = my_program.operand_stack.pop()
    # Creates the SET_SPEED quadruple
    quadruple = Quadruple(my_program.quadruple_number, 'SET_SPEED', operand, None, None)
    my_program.quadruple_list.append(quadruple)
    my_program.quadruple_number += 1

# Check if it is a variable or a string constant and push to operand stack
def p_var_string(p):
    '''var_string : ID pid_action vcv_action
                 | SCONST pso_action'''

# Verify that the variable to push to stack is of type STRING and pushes to stack
def p_vcv_action(p):
    '''vcv_action : '''
    variable = p[-2]
    variable_type = my_program.type_stack[-1]

    # Checks if the variable type is string
    if variable_type != 'string':
        print("The variable: " + variable + " of the color function is not a string")
        sys.exit()

def solve_operation(p):
    """Solve an operation from the stacks"""
    # Gets the operands and its types
    right_operand = my_program.operand_stack.pop()
    right_type = my_program.type_stack.pop()
    left_operand = my_program.operand_stack.pop()
    left_type = my_program.type_stack.pop()

    # Gets the operator
    operator = my_program.operator_stack.pop()

    # Gets the type of the result
    result_type = my_program.semantic_cube.get_semantic_type(left_type ,
        right_type, operator)

    if result_type != 'error':
        #my_program.temporal_variable_counter += 1
        #temporal_variable = "t" + str(my_program.temporal_variable_counter)

        # Gets an address of the temporal memory
        temporal_variable_address = my_program.memory.request_temporal_address(result_type)
        my_program.function_directory.add_temporal_to_function(my_program.current_scope,
            result_type)

        # Creates the quadruple
        quadruple = Quadruple(my_program.quadruple_number, operator, left_operand,
            right_operand , temporal_variable_address)

        # Adds the quadruple to its list and the results to the stacks
        my_program.quadruple_list.append(quadruple)
        my_program.quadruple_number += 1
        my_program.operand_stack.append(temporal_variable_address)
        my_program.type_stack.append(result_type)
    else:
        print('Operation type mismatch at {0}'.format(p.lexer.lineno))
        sys.exit()

def create_conditional_quadruple(p):
    """Creates the quadruple when an if or a while is reached"""
    type_result = my_program.type_stack.pop()

    # It makes no action when the result's type is not a boolean
    if type_result != 'bool':
        print('Operation type mismatch in line {0}'.format(p.lexer.lineno))
        sys.exit();
    else:
        # Creates the GotoF quadruple
        result = my_program.operand_stack.pop()
        quadruple = Quadruple(my_program.quadruple_number, 'GOTOF', result, None, None)
        my_program.quadruple_list.append(quadruple)

        # Stores the number of the GotoF quaduple in order to be filled later
        my_program.jump_list.append(my_program.quadruple_number - 1)
        my_program.quadruple_number += 1

def make_parser():
    parser = yacc.yacc()

    #print("Name of the file to be parsed")
    file_name = input('Please enter the name of the program (.jo as extension): \n')

    with open(file_name) as file_object:
        code = file_object.read()
        parser.parse(code)

    print_quadruples = input('Print intermediate quadruples generated by parser? (Y/N) \n')
    if print_quadruples == 'Y':
        #my_program.function_directory.print_directory()
        #print(str(my_program.temporal_parameters_types))
        #my_program.print_stacks()
        my_program.print_quadruples()
        #my_program.memory.print_memory('global', 'int')

    execute_simulation = input('Execute the simulation? (Y/N) \n')
    if execute_simulation == 'Y':
        execute_step_by_step = input('Print quadruples executed step by step? (Y/N) \n')
        virtual_machine = VirtualMachine(my_program.memory, my_program.function_directory,
            my_program.quadruple_list)
        #virtual_machine.memory.print_memory('global')
        virtual_machine.execute(execute_step_by_step)
        #virtual_machine.memory.print_memory('local', 'int')
        #virtual_machine.memory.print_memory('global', 'int')

    return parser
make_parser()
