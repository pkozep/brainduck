import re
from sys import argv

class BD:
    def __init__( self ) -> None:
        self.last_gen_name = 0
        self.variables = []
        self.code = ""

    # Методы работы с памятью
    def create_variable( self, name: str ) -> int:
        for i in range( len( self.variables ) ):
            if self.variables[i] == name:
                return i * 2
        else:
            self.variables.append( name )
            return self.variables.index( name ) * 2

    def get_variable_index( self, name: str ) -> int:
        return self.variables.index( name ) * 2

    def del_variable( self, name: str ) -> None:
        for i in range( len( self.variables ) ):
            if self.variables[i] == name:
                self.variables[i] = False
                self.set_cursor( i * 2 )
                self.clear_value()

    def gen_variable( self ):
        self.last_gen_name += 1
        name = 'gen_' + str( self.last_gen_name ).zfill( 8 )
        return name, self.create_variable( name )
    
    # Метод преобразует фрагмент кода в последовательность комманд
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
    
    # Метод преобразует код в список команд и исполняет их
    def render_code( self, code ):
        clean_code = code[1:-2].replace( '  ', '' ).replace( '\n', '' )
        commands = self.render_fragment( clean_code )
        for command in commands:
            self.execution(command)
        return self.code

    # Метод выполняет команду
    def execution( self, command, indent: int = 0 ):
        print( '    ' * indent, command ) # Полезно для откладки
        
        def handle_simple_assignment( var_ind: int, expression: str ) -> None:  # Вычисляет значение expression и заносит значение в ячейку с индексом var_ind
            self.set_cursor( var_ind )
            if re.fullmatch( r'\d+', expression ):  # Обработка чисел
                self.add_value( int( expression ) )
            elif re.fullmatch( r'\'[ -~]\'', expression ):  # Обработка символов
                self.add_value( ord( expression[1] ) )
            elif re.fullmatch( r'\w+', expression ):    # Обработка переменных
                self.copy( self.get_variable_index( expression ), var_ind )
            elif re.fullmatch( r'.+ [!=]= .+', expression ):    # Обработка неравенств двух аргументов
                op1, op2 = re.split( r' [!=]= ', expression )
                operation = re.findall( r'[!=]=', expression )[0]
                tmp1, tmp1_ind = self.gen_variable()
                tmp2, tmp2_ind = self.gen_variable()
                handle_simple_assignment( tmp1_ind, op1 )
                handle_simple_assignment( tmp2_ind, op2 )
                self.equality( tmp1_ind, tmp2_ind, var_ind, operation=='==' )
                self.del_variable( tmp1 ), self.del_variable( tmp2 )
            elif re.fullmatch( r'.+ [><] .+', expression ):
                op1, op2 = re.split( r' [><] ', expression )
                operation = re.findall( r'[><]', expression )[0]
                arg1, arg1_ind = self.gen_variable()
                arg2, arg2_ind = self.gen_variable()
                handle_simple_assignment( arg1_ind, op1 )
                handle_simple_assignment( arg2_ind, op2 )
                if operation == '>':
                    self.comparison( arg1_ind, arg2_ind, var_ind )
                else:
                    self.comparison( arg1_ind, arg2_ind, var_ind, False )
                self.del_variable( arg1 ), self.del_variable( arg2 )
            elif re.fullmatch( r'.+ [\+\-\*/] .+', expression ):    # Обработка математических операция (+-*/) для двух аргументов
                op1, op2 = re.split( r' [\+\-\*/] ', expression )
                operation = re.findall( r'[\+\-\*/]', expression )[0]
                tmp, tmp_ind = self.gen_variable()
                if operation == '+':
                    handle_simple_assignment( var_ind, op1 )
                    handle_simple_assignment( var_ind, op2 )
                elif operation == '-':
                    handle_simple_assignment( var_ind, op1 )
                    handle_simple_assignment( tmp_ind, op2 )
                    self.move( tmp_ind, var_ind, False )
                elif operation == '*':
                    handle_simple_assignment( tmp_ind, op1 )
                    self.cycl( tmp_ind, [
                        [ handle_simple_assignment, var_ind, op2 ],
                        [ self.set_cursor, tmp_ind ],
                        [ self.add_value, -1 ]
                    ] )
                elif operation == '/':
                    self.execution( "", indent + 1 )
                self.del_variable( tmp )
            else:
                print( f"Выражение не обработано: \"{ expression }\"" )
    
        if re.fullmatch( r'det \w+', command ):   # det a
            name = command[4:]
            var_ind = self.create_variable( name )
        elif re.fullmatch( r'det \w+ = .*', command ):  # det a = ...
            name, expression = re.split( ' = ', command[4:], maxsplit=1 )
            var_ind = self.create_variable( name )
            handle_simple_assignment( var_ind, expression )
        elif re.fullmatch( r'\w+ = .*', command ):  # a = ...
            name, expression = re.split( ' = ', command, maxsplit=1 )
            var_ind = self.get_variable_index( name )
            handle_simple_assignment( var_ind, expression )
        elif re.fullmatch( r'print .+', command ): # print ...
            expression = command[6:]
            tmp, tmp_ind = self.gen_variable()
            handle_simple_assignment( tmp_ind, expression )
            self.set_cursor( tmp_ind )
            self.print()
            self.del_variable( tmp )
        elif re.fullmatch( r'if .+ \{.*\}', command ):  # if ... {...; ...;}
            cond, body = re.split( r' \{', command[3:], maxsplit=1 )
            body = body.rstrip( '}' )
            tmp, tmp_ind = self.gen_variable()
            handle_simple_assignment( tmp_ind, cond )
            self.cycl( tmp_ind, [
                [ self.set_cursor, tmp_ind ],
                [ self.clear_value ]
            ] + [
                [ self.execution, render_command ] for render_command in self.render_fragment( body ) 
            ] )
            self.del_variable( tmp )
        elif re.fullmatch( r'while .+ \{.*\}', command ):   # while ... {...; ...;}
            cond, body = re.split( ' {', command[6:], maxsplit=1 )
            body = body.rstrip( '}' )
            tmp, tmp_ind = self.gen_variable()
            handle_simple_assignment( tmp_ind, cond )
            self.cycl( tmp_ind, [
                [ self.set_cursor, tmp_ind ],
                [ self.add_value, -1 ] 
            ] + [
                [ self.execution, render_command ] for render_command in self.render_fragment( body.replace( cond, tmp ) )
            ] )
            self.del_variable(tmp )
        else:
            print(f"Команда не обработана: ", command)
        
    # Методы низкоуровневой работы с кодом BF
    def find_cursor( self ) -> int: # Метод находит текущий индекс курсора
        return self.code.count( '>' ) - self.code.count( '<' )
    
    def set_cursor( self, ind: int ) -> None: # Устанавливает курсор на значение ind
        cursor = self.find_cursor()
        self.code += '>' * ( ind - cursor ) + '<' * ( cursor - ind )

    def clear_value( self ) -> None:    # Обнуляет значение в текущей ячейке
        self.code += '[-]'

    def add_value( self, value ) -> None:   # Добавляет значение value в текущую ячейку
        self.code += '+' * value + '-' * ( -value )

    def cycl( self, ind: int, commands: list ) -> None: # Цикл, который выполняет команды пока значение в ячейке ind не будет равно 0
        self.set_cursor( ind )
        self.code += '['
        for command in commands:
            command[0]( *command[1:] )
        self.code += ']'

    def move( self, src: int, dst: int, forward: bool = True ) -> None: # Перемещает значение ячейки src в ячейку dst
        self.cycl( src, [
            [ self.set_cursor, dst ],
            [ self.add_value, forward * 2 - 1 ],
            [ self.set_cursor, src ],
            [ self.add_value, -1 ]
        ] )
    
    def copy( self, src: int, dst: int, forward: bool = True ) -> None: # Копирует значение язейки src в ячейку dst
        tmp = src + 1
        self.cycl( src, [
            [ self.set_cursor, tmp ],
            [ self.add_value, 1 ],
            [ self.set_cursor, dst ],
            [ self.add_value, forward * 2 - 1 ],
            [ self.set_cursor, src ],
            [ self.add_value, -1 ]
        ] )
        self.move( tmp, src )
    
    def equality( self, op1: int, op2: int, output: int, forward: bool = True ) -> None:
        self.copy( op1, output )
        self.copy( op2, output, False )
        self.set_cursor( output )
        if forward:
            self.code += '>+<[>-<[-]]>[-<+>]'
        else:
            self.code += '[>+<[-]]>[-<+>]'

    def comparison( self, op1: int, op2: int, output: int, forward: bool = True ) -> None:
        self.copy( op1, output ), self.copy( op2, output, False ), self.copy( op2, output )
        self.set_cursor( output )
        self.add_value( -1 )
        self.code += '@'
        if forward:
            self.code += '[>+<[-]]>[-<+>]'
        else:
            self.code += '>+<[>-<[-]]>[-<+>]'

    def print( self ) -> None:
        self.code += '.'

    def input( self ) -> None:
        self.code += ','

if __name__ == "__main__":  # python main -i "input_file" -o "output_file"
    for i in range(1, 4, 2):
        if argv[i] == "-i":
            input_file = argv[i + 1]
        if argv[i] == "-o":
            output_file = argv[i + 1]

    bd = BD()
    with open( input_file, 'r', encoding="utf-8" ) as file:
        code = file.read()
    
    with open( output_file, 'w', encoding="utf-8" ) as file:
        file.write( bd.render_code( code ) + '@' )
    