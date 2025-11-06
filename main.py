import re
from sys import argv

BUFF_SIZE = 12

class BD:
    def __init__( self ) -> None:
        self.buff = [ 0 ] * 2 + [ 1 ] * ( BUFF_SIZE - 1 )
        self.memory = [ 'cursorFreeSpace' ] + self.buff
        self.code = "+" * ( 1 + BUFF_SIZE )
        self.cursorPosition = 0

    def create_variable( self, nameVar: str, sizeVar: int = 1 ) -> int:
        self.memory += [ nameVar ] * sizeVar
        self.add_value( 0, sizeVar )
        return self.memory.index( nameVar ) * 2
        
    def get_variable_index( self, nameVar: str ) -> int:
        return self.memory.index( nameVar ) * 2
        
    def get_buff( self, size: int ) -> int:
        result = []
        count = 0
        for index in range( BUFF_SIZE ):
            if self.buff[ index ]:
                self.buff[ index ] = 0
                result.append( (1 + index) * 2 )
                count += 1
            if count == size:
                break
        else:
            raise "Нехватка буфферных переменных!"
        return result

    def empty_buff( self, index: list[int] ) -> None:
        for i in index:
            self.buff[ i//2 - 1 ] = 1
            self.set_value( i, 0 )

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
                commands.append( word )
                word = ""
                continue
            word += char
        return commands

    def render_code( self, code ):
        clean_code = code.replace( '  ', '' ).replace( '\n', '' )
        commands = self.render_fragment( clean_code )
        for command in commands:
            self.execution( command ), print( command )
        return self.code
    
    def execution( self, command ) -> None:
        def handle_simple_assignment( var_ind: int, expression: str ) -> None:
            if re.fullmatch( r"&.+", expression ):
                name = expression[ 1: ]
                self.add_value( var_ind, self.get_variable_index( name )//2 )
            elif re.fullmatch( r"\d+", expression ):
                tmp = self.get_buff( 1 )
                self.add_value( var_ind, int( expression ) )
                self.empty_buff( tmp )
            elif re.fullmatch( r"\'[ -~]\'", expression ):
                tmp = self.get_buff( 1 )
                self.add_value( var_ind, ord( expression[1] ) )
                self.empty_buff( tmp )
            elif re.fullmatch( r"\w+", expression ):
                self.copy( self.get_variable_index( expression ), var_ind )
            elif re.fullmatch( r".+ [!=]= .+", expression ):
                op1, op2 = re.split( r" [!=]= ", expression )
                operation = re.findall( r"[!=]=", expression )[ 0 ]
                tmp = self.get_buff( 2 )
                handle_simple_assignment( tmp[ 0 ], op1 )
                handle_simple_assignment( tmp[ 1 ], op2 )
                if operation == "==":
                    self.equality( tmp[ 0 ], tmp[ 1 ], var_ind )
                else:
                    self.equality( tmp[ 0 ], tmp[ 1 ], var_ind, False )
                self.empty_buff( tmp )
            elif re.fullmatch( r".+ [><] .+", expression ):
                op1, op2 = re.split( r" [><] ", expression )
                operation = re.findall( r"[><]", expression )[ 0 ]
                tmp = self.get_buff( 2 )
                handle_simple_assignment( tmp[ 0 ], op1 )
                handle_simple_assignment( tmp[ 1 ], op2 )
                if operation == '>':
                    self.comparison( tmp[ 0 ], tmp[ 1 ], var_ind )
                else:
                    self.comparison( tmp[ 1 ], tmp[ 0 ], var_ind )
                self.empty_buff( tmp )
            elif re.fullmatch( r".+ [><]= .+", expression ):
                op1, op2 = re.split( r" [><]= ", expression )
                operation = re.findall( r"[><]", expression )[ 0 ]
                tmp = self.get_buff( 2 )
                handle_simple_assignment( tmp[ 0 ], op1 )
                handle_simple_assignment( tmp[ 1 ], op2 )
                if operation == '>':
                    self.comparison( tmp[ 1 ], tmp[ 0 ], var_ind, False )
                else:
                    self.comparison( tmp[ 0 ], tmp[ 1 ], var_ind, False )
                self.empty_buff( tmp )
            elif re.fullmatch( r".+ [\+\-\*/] .+", expression ):
                op1, op2 = re.split( r" [\+\-\*/] ", expression, maxsplit=1 )
                operation = re.findall( r"[\+\-\*/]", expression )[ 0 ]
                if operation == '+':
                    tmp = self.get_buff( 1 )
                    handle_simple_assignment( tmp[ 0 ], op1 )
                    handle_simple_assignment( tmp[ 0 ], op2 )
                    self.move( tmp[ 0 ], var_ind )
                    self.empty_buff( tmp )
                elif operation == '-':
                    tmp = self.get_buff( 2 )
                    handle_simple_assignment( tmp[ 0 ], op1 )
                    self.move( tmp[ 0 ], var_ind )
                    handle_simple_assignment( tmp[ 0 ], op2 )
                    self.move( tmp[ 0 ], var_ind, False )
                    self.empty_buff( tmp )
                elif operation == '*':
                    tmp = self.get_buff( 2 )
                    handle_simple_assignment( tmp[ 0 ], op1 )
                    handle_simple_assignment( tmp[ 1 ], op2 )
                    self.cycle_for( tmp[ 0 ], [
                        [ self.copy, tmp[ 1 ], var_ind ]
                    ] )
                    self.empty_buff( tmp )
                elif operation == '/':
                    tmp = self.get_buff( 4 )
                    handle_simple_assignment( tmp[ 0 ], op1 )
                    handle_simple_assignment( tmp[ 1 ], op2 )
                    handle_simple_assignment( tmp[ 2 ], "128" )
                    self.copy( tmp[ 1 ], tmp[ 0 ], False )
                    self.comparison( tmp[ 0 ], tmp[ 2 ], tmp[ 3 ], False )
                    self.cycle_while( tmp[ 3 ], [
                        [ self.set_value, tmp[ 3 ], 0 ],
                        [ self.copy, tmp[ 1 ], tmp[ 0 ], False ],
                        [ self.comparison, tmp[ 0 ], tmp[ 2 ], tmp[ 3 ], False ],
                        [ self.add_value, var_ind, 1 ]
                    ] )
                    self.empty_buff( tmp )
            elif re.fullmatch( r"new\(\d+\)", expression ):
                size = int( re.findall( r"\d+", expression )[ 0 ] )
                self.copy( 0, var_ind )
                self.add_value( 0, size )
            elif re.fullmatch( r"\*\w+", expression ):
                name = expression[ 1: ]
                self.get_value_dynamic( self.get_variable_index( name ), var_ind )
            else:
                print( f"Выражение не обработано: \"{ expression }\"" )
        
        if re.fullmatch( r"det\[\d+\] \w+", command ):
            size, name = command[3:].split()
            var_ind = self.create_variable( name, int( size[ 1:-1 ] ) )
        elif re.fullmatch( r"det\[\d+\] \w+ = .*", command ):
            size_and_name, expression = re.split( r" = ", command, maxsplit=1 )
            size, name = size_and_name[3:].split()
            var_ind = self.create_variable( name, int( size[ 1:-1 ] ) )
            handle_simple_assignment( var_ind, expression )
        elif re.fullmatch( r"\w+ = .*", command ):
            name, expression = re.split( ' = ', command, maxsplit=1 )
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], expression )
            self.set_value( self.get_variable_index( name ), 0 )
            self.move( tmp[ 0 ], self.get_variable_index( name ) )
            self.empty_buff( tmp )
        elif re.fullmatch( r"\w+\[\d+\] = .*", command ):
            name_and_index, expression = re.split( ' = ', command, maxsplit=1 )
            name, index = re.findall( r"\w+", name_and_index )[ 0 ], re.findall( r"\[\d+\]", name_and_index )[0]
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], expression )
            self.set_value( self.get_variable_index( name ) + int( index[ 1:-1 ] ) * 2, 0 )
            self.move( tmp[ 0 ], self.get_variable_index( name ) + int( index[ 1:-1 ] ) * 2 )
            self.empty_buff( tmp )
        elif re.fullmatch( r"\w+\[\w+\] = .*", command ):
            name_and_index, expression = re.split( ' = ', command, maxsplit=1 )
            name, index = re.findall( r"\w+", name_and_index )[ 0 ], re.findall( r"\[\w+\]", name_and_index )[0]
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], expression )
            self.add_value( 1, self.get_variable_index( name )//2 )
            self.clear_value_dynamic( self.get_variable_index( index[ 1:-1 ] ) )
            self.add_value( 1, self.get_variable_index( name )//2 )
            self.copy_value_dynamic( tmp[0], self.get_variable_index( index[ 1:-1 ] ) )
            self.empty_buff( tmp )
        elif re.fullmatch( r"\*\w+ = .*", command ):
            name, expression = re.split( ' = ', command[ 1: ], maxsplit=1 )
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], expression )
            self.clear_value_dynamic( self.get_variable_index( name ) )
            self.copy_value_dynamic( tmp[ 0 ], self.get_variable_index( name ) )
            self.empty_buff( tmp )
        elif re.fullmatch( r"\*\w+\[\d+\] = .*", command ):
            name_and_index, expression = re.split( ' = ', command, maxsplit=1 )
            name, index = re.findall( r"\w+", name_and_index )[ 0 ], re.findall( r"\[\d+\]", name_and_index )[0]
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], expression )
            self.add_value( 1, int( index[ 1:-1 ] ) )
            self.clear_value_dynamic( self.get_variable_index( name ) )
            self.add_value( 1, int( index[ 1:-1 ] ) )
            self.copy_value_dynamic( tmp[0], self.get_variable_index( name ) )
            self.empty_buff( tmp )
        elif re.fullmatch( r"\*\w+\[\w+\] = .*", command ):
            name_and_index, expression = re.split( ' = ', command, maxsplit=1 )
            name, index = re.findall( r"\w+", name_and_index )[ 0 ], re.findall( r"\[\w+\]", name_and_index )[0]
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], expression )
            self.copy( self.get_variable_index( name ), 1 )
            self.clear_value_dynamic( self.get_variable_index( index[ 1:-1 ] ) )
            self.copy( self.get_variable_index( name ), 1 )
            self.copy_value_dynamic( tmp[0], self.get_variable_index( index[ 1:-1 ] ) )
            self.empty_buff( tmp )
        elif re.fullmatch( r"\w+ [\+\-\*/]= .*", command ):
            name, expression = re.split( r' [\+\-\*/]= ', command, maxsplit=1 )
            operation = re.findall( r' [\+\-\*/]= ', command )[ 0 ][ 1 ]
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], f"{name} {operation} {expression}")
            self.set_value( self.get_variable_index( name ), 0 )
            self.copy( tmp[ 0 ], self.get_variable_index( name ) )
            self.empty_buff( tmp )
        elif re.fullmatch( r"if .+ \{.*\}", command ):
            cond, body = re.split( r' \{', command[ 3: ], maxsplit=1 )
            body = body.rstrip( '}' )
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], cond )
            self.conditions( tmp[ 0 ], [
                [ self.execution, render_command ] for render_command in self.render_fragment( body ) 
            ] )
            self.empty_buff( tmp )
        elif re.fullmatch( r"while .+ \{.*\}", command ):
            cond, body = re.split( ' {', command[ 6: ], maxsplit=1 )
            body = body.rstrip( '}' )
            tmp = self.get_buff( 1 )
            handle_simple_assignment( tmp[ 0 ], cond )
            self.cycle_while( tmp[ 0 ], [
                [ self.execution, render_command ] for render_command in self.render_fragment( body )
            ] + [
                [ self.set_value, tmp[0], 0 ],
                [ handle_simple_assignment, tmp[ 0 ], cond ]
            ] )
            self.empty_buff( tmp )
        else:
            print(f"Команда не обработана: ", command)

    def set_cursor( self, index: int ) -> None:
        self.code += '>' * ( index - self.cursorPosition ) + '<' * ( self.cursorPosition - index )
        self.cursorPosition = index

    def clear_value( self ) -> None:
        self.code += "[-]"

    def add_value( self, index: int, value: int ) -> None:
        self.set_cursor( index )
        self.code += '+' * value + '-' * ( -value )

    def set_value( self, index: int, value: int ) -> None:
        self.set_cursor( index )
        self.clear_value()
        self.add_value( index, value )

    def cycle_while( self, index: int, commands: list ) -> None:
        self.set_cursor( index )
        self.code += '['
        for command in commands:
            command[0]( *command[1:] ) 
        self.set_cursor( index )
        self.code += ']'

    def cycle_for( self, index: int, commands: list ) -> None:
        self.set_cursor( index )
        self.code += '['
        for command in commands:
            command[0]( *command[1:] ) 
        self.add_value( index, -1 ) 
        self.code += ']'

    def conditions( self, index: int, commands: list ) -> None:
        self.set_cursor( index )
        self.code += '['
        for command in commands:
            command[0]( *command[1:] ) 
        self.set_value( index, 0 ) 
        self.code += ']'

    def move( self, src: int, dst: int, forward: bool = True ) -> None:
        self.cycle_for( src, [
            [ self.add_value, dst, forward * 2 - 1 ]
        ] )

    def copy( self, src: int, dst: int, forward: bool = True ) -> None:
        tmp = src + 1
        self.cycle_for( src, [
            [ self.add_value, tmp, 1 ],
            [ self.add_value, dst, forward * 2 - 1 ]
        ] )
        self.move( tmp, src )

    def equality( self, op1: int, op2: int, output: int, forward: bool = True ) -> None:
        self.copy( op1, output )
        self.copy( op2, output, False )
        self.set_cursor( output )
        self.cursorPosition += 1
        self.code += '>+<[>-<[-]]>[-<+>]' if forward else '[>+<[-]]>[-<+>]'

    def comparison( self, op1: int, op2: int, output: int, forward: bool = True ) -> None:
        # self.code += op1 > op2 if forward else op1 <= op2
        tmp = self.get_buff( 3 )
        self.add_value( tmp[ 0 ], 1 )
        self.copy( op1, tmp[ 1 ] )
        self.copy( op2, tmp[ 1 ] + 1 )
        self.set_cursor( tmp[ 0 ] )
        if forward:
            self.code += ">>[[->]<<]<[->]+<[>-<-]"
        else:
            self.code += ">>[[->]<<]<[->]+<[>+<-]>-<"
        self.set_value( tmp[ 1 ], 0 )
        self.set_value( tmp[ 1 ] + 1, 0 )
        self.move( tmp[ 0 ] +  1, output )
        self.empty_buff( tmp )

    def print_value( self ) -> None:
        self.code += '.'

    def input_value( self ) -> None:
        self.code += ','

    def copy_value_dynamic( self, src: int, dst: int ) -> None: 
        self.copy( dst, 1 )
        self.copy( src, 5 )
        self.set_cursor( 1 )
        self.code += '-[->>+<<]+>>>>[->>+<<]<<[-[->>+<<]>>>>[->>+<<]<<]>>>>[-<<<<<+>>>>>]<<<<<'
        self.exit_dynamic()

    def get_value_dynamic( self, src: int, dst: int ) -> None:
        self.copy( src, 1 )
        self.set_cursor( 1 )
        self.code += '-[->>+<<]+>>[-[->>+<<]>>]<[->+<]>[<+<+>>-]<'
        self.code += '<-[>>>>[-<<+>>]<<<<+<<-]<'
        self.cursorPosition = 0
        self.move( 5, dst )

    def clear_value_dynamic( self, index: int ) -> None:
        self.copy( index, 1 )
        self.set_cursor( 1 )
        self.code += '-[->>+<<]+>>[-[->>+<<]>>]<'
        self.code += '[-]'
        self.exit_dynamic()

    def exit_dynamic( self ) -> None:
        self.code += '<-[+<<-]<'
        self.cursorPosition = 0

if __name__ == "__main__":
    for i in range(1, 4, 2):
        if len( argv ) == 5:
            if argv[i] == "-i": input_file = argv[i + 1]
            if argv[i] == "-o": output_file = argv[i + 1]
        else:
            raise "Необходимо передать -i <входной файл> и -o <выходной файд>"
        
    bd_compil = BD()
    with open( input_file, 'r', encoding="utf-8" ) as file:
        code = file.read()

    with open( output_file, 'w' ) as file:
        file.write( bd_compil.render_code( code ) + '"' )
