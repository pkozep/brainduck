import re

class BrainDuck:
    def __init__( self ):
        self.variables = []
        self.code = ""
        self.last_gen_name = 0
    
    def create_variable( self, name: str, size: int = 1 ) -> list[int]:
        free_start, free_count = -1, 0
        for i, isOccupied in enumerate( self.variables ):
            if not isOccupied:
                free_count += 1
                if free_count == size:
                    free_start = i - size + 1
                    break
            else:
                free_count = 0
        
        if free_start == -1:
            free_start = len( self.variables )
            self.variables.extend( [False] * size )
        for i in range( free_start, free_start + size ):
            self.variables[i] = name

        return [ i * 2 for i, var in enumerate( self.variables ) if var == name ]

    def get_variable_index( self, name: str ) -> list[int]:
        return [ i * 2 for i, var in enumerate( self.variables ) if var == name ]

    def del_variable( self, name: str ) -> None:
        for i, var in enumerate( self.variables ):
            if var == name:
                self.variables[i] = False
                self.set_cursor( i * 2 )
                self.clear_value()

    def gen_name( self ):
        self.last_gen_name += 1
        return 'gen_' + str( self.last_gen_name ).zfill( 8 )
    
    def render_fragment( self, fragment: str ) -> list:
        commands = []
        word = ""
        brace_count = 0
        for char in fragment:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == ';' and brace_count == 0 and word:
                commands.append(word)
                word = ""
                continue
            word += char
        return commands
    
    ### execution the command
    def render( self, code ):
        clean_code = code[1:-2].replace( '  ', '' ).replace( '\n', '' )
        commands = self.render_fragment( clean_code )
        print( commands )
        for command in commands:
            self.execution(command)

    def execution( self, command, indent: int = 0 ):
        print( '    ' * indent, command )
        def parse_name_and_index( expr ):
            match = re.match( r'(\w+)(?:\[(\d+)\])?', expr )
            name, index = match.groups()
            return name, int( index )

        def handle_simple_assignment( var_ind: list[int], expression: str ) -> None:
            print('    ' * ( indent +1) + "Выражение:", expression)
            self.set_cursor( var_ind[0] )
            self.clear_value()
            if re.fullmatch( r'\d+', expression ):
                self.add_value( int( expression ) )
            elif re.fullmatch( r'\'[ -~]\'', expression ):
                self.add_value( ord( expression[1] ) )
            elif re.fullmatch( r'\".*\"', expression ):
                for i, char in enumerate( expression[1:-1] ):
                    self.set_cursor( var_ind[i] )
                    self.add_value( ord( char ) )
            elif re.fullmatch( r'\{\d+(, \d+)*\}', expression ):
                values = expression.strip( '{}' ).split( ', ' )
                for i, value in enumerate( values ):
                    self.set_cursor( var_ind[i] )
                    self.add_value( int( value ) )
            elif re.fullmatch( r'\w+\[\d+\]', expression ):
                src_name, src_idx = parse_name_and_index( expression )
                src_index = self.get_variable_index( src_name ) + src_idx * 2
                self.copy( src_index, var_ind )
            elif re.fullmatch( r'\w+', expression ):
                for i in range( len( var_ind ) ):
                    self.copy( self.get_variable_index( expression )[i], var_ind[i] )
            elif re.fullmatch( r'.+ [=\!]= .+', expression ):
                op1, op2 = re.split( r'[=\!]=', expression )
                buff1, buff2 = self.gen_name(), self.gen_name()
                var1_ind, var2_ind = self.create_variable( buff1 ), self.create_variable( buff2)
                handle_simple_assignment( var1_ind, op1.strip() )
                handle_simple_assignment( var2_ind, op2.strip())
                self.move(var2_ind[0], var1_ind[0], False)
                self.set_cursor(var_ind[0])
                if re.findall( r'[!=]=', expression )[0][0] != '!':
                    self.add_value(1)
                    self.condition( var1_ind[0], [[self.set_cursor, var_ind[0]], [self.add_value, -1],[self.set_cursor, var1_ind[0]], [self.clear_value]])
                else:
                    self.condition( var1_ind[0], [[self.set_cursor, var_ind[0]], [self.add_value, 1],[self.set_cursor, var1_ind[0]], [self.clear_value]])
                self.del_variable( buff1 ), self.del_variable( buff2)
            elif re.fullmatch( r'.+ [\+\-\*/] .+', expression ):
                op1, op2 = re.split( r'[\+\-\*/]', expression )
                buff1, buff2 = self.gen_name(), self.gen_name()
                var1_ind, var2_ind = self.create_variable( buff1 ), self.create_variable( buff2 )
                handle_simple_assignment( var1_ind, op1.strip() )
                handle_simple_assignment( var2_ind, op2.strip() )
                if re.findall( r'[\+\-\*/]', expression )[0] == '+':
                    self.move( var1_ind[0], var_ind[0] )
                    self.move( var2_ind[0], var_ind[0] )
                elif re.findall( r'[\+\-\*/]', expression )[0] == '-':
                    self.move( var1_ind[0], var_ind[0] )
                    self.move( var2_ind[0], var_ind[0], False )
                elif re.findall( r'[\+\-\*/]', expression )[0] == '*':
                    self.iterate( var1_ind[0], [ [ self.copy, var2_ind[0], var_ind[0] ] ] )
                elif re.findall( r'[\+\-\*/]', expression )[0] == '/':
                    pass
                self.del_variable( buff1 ), self.del_variable( buff2 )
            else:
                print( f"Выражение не обработано: \"{ expression }\"" )

        if re.fullmatch( r'det \w+(\[\d+\])?', command ):   # det a # det a[3]
            name = re.findall( r"\w+", command )[1]
            if re.fullmatch( r"det \w+\[\d+\]", command ):
                size = int( re.findall( r'\[\d+\]', command )[0].strip( '[]' ) )
            else:
                size = 1
            self.create_variable( name, size )
        elif re.fullmatch( r'det \w+ = .*', command ):  # det a = ...
            name = re.findall( r"\w+", command )[1]
            expression = command.split( ' = ', 1 )[1]
            self.execution( f"det { name }", indent + 1 )
            self.execution( f"{ name } = { expression }", indent + 1 )
        elif re.fullmatch( r'det \w+\[\d+\] = .*', command ):  # det a[3] = ...
            name = re.findall( r"\w+", command )[1]
            len_array = int( re.findall( r'\[\d+\]', command )[0].strip( '[]' ) )
            expression = command.split( ' = ', 1 )[1]
            self.execution( f"det { name }[{ len_array }]", indent + 1 )
            self.execution( f"{ name } = { expression }", indent + 1 )
        elif re.fullmatch( r'\w+ = .*', command ):  # a = ...
            name, expression = command.split( ' = ', 1 )
            var_ind = self.get_variable_index( name )
            handle_simple_assignment( var_ind, expression )
        elif re.fullmatch( r'\w+ = .*', command ):  # a[3] = ...
            name, index = command[:-1].split( '[' )
            expression = command.split( ' = ', 1 )[1]
            var_ind = self.get_variable_index( name )
            self.set_cursor( var_ind )
            handle_simple_assignment( var_ind + index * 2, expression )
        elif re.fullmatch( r'cout( << .+)+', command ): # cout << ... << ...
            params = command[4:].lstrip( ' << ' ).split( ' << ' )
            buff = self.gen_name()
            self.create_variable( buff )
            var_id = self.get_variable_index( buff )
            for param in params:
                handle_simple_assignment( var_id, param )
                self.print()
            self.del_variable( buff )
        elif re.fullmatch( r'if .+ \{.*\}', command ):  # if ... {...; ...;}
            cond, body = re.split( r' \{', command[3:], maxsplit=1 )
            body = body.rstrip( '}' )
            buff = self.gen_name()
            self.create_variable(buff)
            handle_simple_assignment( self.get_variable_index( buff ), cond )
            self.condition( self.get_variable_index( buff )[0], [ [ self._execute_command, render_command ] for render_command in self.render_fragment( body ) ] )
            self.del_variable( buff )
        elif re.fullmatch( r'while .+ \{.*\}', command ):   # while ... {...; ...;}
            cond, body = re.split( ' {', command[6:], maxsplit=1 )
            body = body.rstrip( '}' )
            buff = self.gen_name()
            self.create_variable( buff )
            handle_simple_assignment( self.get_variable_index( buff ), cond )
            self.condition( self.get_variable_index( buff )[0], [ [ self._execute_command, render_command ] for render_command in self.render_fragment( body.replace( cond, buff ) ) ] +  [ [ self._execute_command, f"{buff} = {cond}"] ] + [[self.set_cursor, self.get_variable_index( buff )[0]]] )
            self.del_variable( buff )
        elif re.fullmatch( r'\w+ [\+\-\*/]= .+', command ):  # a += ...
            name, expression = re.split(r' [\+\-\*/]= ', command)
            op = re.findall(r' [\+\-\*/]= ', command)[0][1]
            buff = self.gen_name()
            self.create_variable( buff )
            self._execute_command( f"{buff} = {name} {op} {expression}" )
            self._execute_command( f"{name} = {buff}" )
            self.del_variable( buff )
        else:
            print(f"Команда не обработана: ", command)
        
    ### Methods
    def find_cursor( self ) -> int:
        return self.code.count( '>' ) - self.code.count( '<' )
    
    def set_cursor( self, ind: int ) -> None:
        cursor = self.find_cursor()
        self.code += '>' * ( ind - cursor ) + '<' * ( cursor - ind )

    def clear_value( self ) -> None:
        self.code += '[-]'
    
    def add_value( self, value ) -> None:
        self.code += '+' * value + '-' * ( -value )

    def _execute_command( self, command: str ) -> None:
        self.execution( command )

    def condition( self, ind: int, commands: list[list] ) -> None:
        self.set_cursor( ind )
        self.code += '['
        for command in commands:
            command[0]( *command[1:] )
        self.code += ']'

    def iterate( self, ind: int, commands: list[str] ) -> None:
        self.condition( ind, commands + [ [ self.set_cursor, ind ], [ self.add_value, -1 ] ] )

    def move( self, src: int, dst: int, forward: bool = True ) -> None:
        self.iterate( src, [ [ self.set_cursor, dst ], [ self.add_value, forward * 2 - 1 ] ] )

    def copy( self, src: int, dst: int, forward: bool = True ) -> None:
        temp = src + 1
        self.iterate( src, [ [ self.set_cursor, temp ], [ self.add_value, 1 ], [ self.set_cursor, dst ], [ self.add_value, forward * 2 - 1 ] ] )
        self.move( temp, src )

    def equality( self, op1: int, op2: int, output: int, forward: bool = True ) -> None:
        self.copy( op1, output )
        self.copy( op2, output, False )
        self.set_cursor( output )
        
        if forward:
            self.code += '>+<[>-<[-]]>[-<+>]'
        else:
            self.code += '[>+<[-]]>[-<+>]'

    def print( self ) -> None:
        self.code += '.'

    def input( self ) -> None:
        self.code += ','

code = BrainDuck()

with open( 'test.bd', 'r' ) as file:
    code.render( file.read() )

print( *code.variables )
print( code.code )