import re
import random

class BrainDuck:
    def __init__( self ):
        self.params = []
        self.code = ''

    # Compiler params management methods
    def add_param( self, name, tp ):
        for i in range( len( self.params ) ):
            if self.params[ i ][ 1 ] == None:
                self.params[ i ] = [ name, tp ]
                break
        else:
            self.params.append( [ name, tp ] )

    def add_array( self, name, tp_and_size ):
        tp, size = tp_and_size[:-1].split( '[' )
        max_free_size = 0
        start_ind = 0
        for i in range( len( self.params ) ):
            if self.params[ i ][ 1 ] == None:
                max_free_size += 1
            else:
                max_free_size = 0
                start_ind = i + 1
            if max_free_size == int( size ):
                break
        else:
            for i in range( int( size ) ):
                self.params.append( [ name, tp_and_size ] )
            return True
        
        for i in range( len( self.params ) ):
            if i >= start_ind and i < start_ind + int( size ):
                self.params[ i ] = [ name, tp ]


    def get_param( self, name ):
        for i in range( len( self.params ) ):
            if self.params[ i ][ 0 ] == name:
                return i * 2
    
    def del_param( self, name ):
        for i in range( len( self.params ) ):
            if self.params[ i ][ 0 ] == name:
                self.params[ i ][ 1 ] = None
                self.clear_value( i*2 )
    
    # Executing the command
    def execution( self, command ):
        print( command )
        if re.fullmatch( r"^(int|char) [a-zA-Z_][a-zA-Z0-9_]*;$", command ):
            # int a;  # char a;
            tp, name = command[:-1].split()
            self.add_param( name, tp )
        elif re.fullmatch( r"^(int|char) [a-zA-Z_][a-zA-Z0-9_]*\[\d+\];$", command ):
            # int a[10];  # char a[10];
            tp, name_and_size = command[:-1].split()
            name, size = name_and_size[:-1].split( '[' )
            self.add_array( name, tp + f"[{ size }]" )
        elif re.fullmatch( r"^(int|char) [a-zA-Z_][a-zA-Z0-9_]* = (.*);$", command ):
            # int a = ...;  # char a = ...;
            tp_and_name, expression = command[:-1].split( ' = ' )
            tp, name = tp_and_name.split()
            self.execution( f"{ tp } { name };" )
            self.execution( f"{ name } = { expression };" )
        elif re.fullmatch( r"^int [a-zA-Z_][a-zA-Z0-9_]*\[\d+\] = \{(\d+(?:, \d+)*)\};$", command ):
            # int a[12] = {...};
            tp_and_name, expression = command[:-1].split( ' = ' )
            tp, name_and_size = tp_and_name.split()
            name, size = name_and_size[:-1].split( '[' )
            self.execution( f"{ tp } { name_and_size };" )
            for i in range( len( expression[1:-1].split( ', ' ) ) ):
                self.execution( f"{ name }[{ i }] = { expression[1:-1].split( ', ' )[ i ] };" )
        elif re.fullmatch( r"^char [a-zA-Z_][a-zA-Z0-9_]*\[\d+\] = (.*);$", command ):
            # char a[12] = "...";
            tp_and_name, expression = command[:-1].split( ' = ' )
            tp, name_and_size = tp_and_name.split()
            name, size = name_and_size[:-1].split( '[' )
            self.execution( f"{ tp } { name_and_size };" )
            for i in range( 1, len( expression ) - 1 ):
                self.execution( f"{ name }[{ i - 1 }] = '{ expression[ i ] }';" )
        elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* = (.*);$", command ):
            # a = ...;
            name, expression = command[:-1].split( ' = ' )
            if re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* = \d+;$", command ):
                # a = 123;
                self.set_value( self.get_param( name ), int( expression ) )
            elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* = \'[ -~]\';$", command ):
                # a = 'A';
                self.set_value( self.get_param( name ), ord( expression[1] ) )
            elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* = [a-zA-Z_][a-zA-Z0-9_]*;$", command ):
                # a = b;
                self.copy( self.get_param( expression ), self.get_param( name ) )
            elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* = [a-zA-Z_][a-zA-Z0-9_]*\[\d+\];$", command ):
                # a = b[3];
                name_param, index_param = expression[:-1].split( '[' )
                self.copy( self.get_param( name_param ) + int( index_param )*2, self.get_param( name ) )
            elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* = [-]* \d+ [\+\-\*\\] \d+( [\+\-\*\\] \d+)*$", command ):
                # a = . + . - . * . \ .;
                if expression[0] != '-':
                    expression = ' + ' + expression
                else:
                    expression = ' ' + expression
                params = expression.split( ' + ' )
                buff = BrainDuck.gen_name()
                self.execution( f"int { buff };" )
                self.execution( f"{ buff } += { params[0] };" )
                self.execution( f"{ buff } += { params[1] };" ) 
                self.copy( self.get_param( buff ), self.get_param( name ) )
                self.del_param( buff )
        elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]*\[\d+\] = (.*);$", command ):
            # a[3] = ...;
            name, expression = command[:-1].split( ' = ' )
            name, index = name[:-1].split( '[' )
            buff = BrainDuck.gen_name()
            self.execution( f"{ buff} = { expression };" )
            self.copy( self.get_param( buff ), self.get_param( name ) + int( index )*2 )
            self.del_param( buff )
        elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* \+= (.*);$", command ):
            # a += ...;
            name, expression = command[:-1].split( ' += ' )
            buff = BrainDuck.gen_name()
            self.execution( f"int { buff} = { expression };" )
            self.copy( self.get_param( buff ), self.get_param( name ) )
            self.del_param( buff )
        elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* \-= (.*);$", command ):
            # a -= ...;
            name, expression = command[:-1].split( ' -= ' )
            buff = BrainDuck.gen_name()
            self.execution( f"int { buff} = { expression };" )
            self.copy( self.get_param( buff ), self.get_param( name ), False )
            self.del_param( buff )
        elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* \*= (.*);$", command ):
            # a *= ...;
            name, expression = command[:-1].split( ' *= ' )
            buff = BrainDuck.gen_name()
            self.execution( f"int { buff} = { expression };" )
            # wait
            self.del_param( buff )
        elif re.fullmatch( r"^[a-zA-Z_][a-zA-Z0-9_]* \\= (.*);$", command ):
            # a \= ...;
            name, expression = command[:-1].split( ' \\= ' )
            buff = BrainDuck.gen_name()
            self.execution( f"int { buff} = { expression };" )
            # wait
            self.del_param( buff )
        

    # Methods 
    def find_cursor( self ):
        return self.code.count( '>' ) - self.code.count( '<' )
    
    def set_cursor( self, ind ):
        cursor = self.find_cursor()
        self.code += '>' * ( ind - cursor ) + '<' * ( cursor - ind )

    def add_value( self, ind, value ):
        self.set_cursor( ind )
        self.code += '+' * value + '-' * ( -value )

    def clear_value( self, ind ):
        self.set_cursor( ind )
        self.code += '[-]'

    def set_value( self, ind, value ):
        self.clear_value( ind )
        self.add_value( ind, value )

    def iterate( self, ind, commands ):
        self.set_cursor( ind )
        self.code += "["
        for command in commands:
            if isinstance( command, str ):
                self.compile( command )
            else:
                command[ 0 ]( *command[ 1: ] )
        self.set_cursor( ind )
        self.code += "-]"
    
    def move( self, where_from, where ):
        self.iterate( where_from, [ [ self.add_value, where, 1 ] ] )

    def copy( self, where_from, where, forward=True ):
        self.iterate( where_from, [ [ self.add_value, where_from + 1, 1 ], [ self.add_value, where, forward*2 - 1 ] ] )
        self.move( where_from + 1, where_from )

    def equality( self, operand1, operand2, output, forward=True ):
        self.clear_value( output )
        self.copy( operand1, output )
        self.copy( operand2, output, False )
        self.set_cursor( output )
        if forward:
            self.code += ">+<[>-<[-]]>[-<+>]"
        else:
            self.code += "[>+<[-]]>[-<+>]"

    def comparison( self, operand1, operand2, output, strictly, forward=True ):
        pass

    @staticmethod
    def gen_name():
        return "gen_" + str( hash( random.random() ) )
    
bd = BrainDuck()

with open( 'test', 'r' ) as file:
    for command in file.read().split('\n'):
        bd.execution( command )

print( bd.params )
print( bd.code )