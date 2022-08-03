
__all__ = [
	'CommandBuilder', 'WhereBuilder',
	'FieldBuilder',
	'create', 'drop',
	'delete', 'insert', 'select', 'update'
]

class CommandBuilder: pass
class WhereBuilder: pass
class FieldBuilder: pass

class CommandBuilder:
	'''
	Sql command builder, direct instantiation is not recommended

	Attributes:
		command: The command to execute
		values: The format values to execute

	Usage:
		cmd = <CommandBuilder>
		cursor.execute(cmd.command, cmd.values)

	See also:
		create, drop, delete, insert, select, update
	'''
	def __init__(self, cmd: str, /):
		self.command = cmd
		self.values = []
		self._where_exists = False

	def __str__(self):
		return self.command

	def __repr__(self):
		return f'<CommandBuilder "{self.command}">'

	def append(self, arg, *, prev=' ') -> CommandBuilder:
		'''
		Append a value to command

		Args:
			arg: The word to append
			prev: The prev char

		Return:
			CommandBuilder: self

		Usage:
			<CommandBuilder>.append('KEYWORD1').append('KEYWORD2')
		'''
		self.command += prev + arg
		return self

	def name(self, *args, prev=' ', sep=' ') -> CommandBuilder:
		'''
		Append names to command, use format \`name\`

		Args:
			args: The names to append
			prev: The prev char
			sep: The sep char between names

		Return:
			CommandBuilder: self

		Alias:
			CommandBuilder.k

		Usage:
			<CommandBuilder>.name('key1', 'key2').name('key3')
		'''
		self.command += prev + sep.join(f'`{k}`' for k in args)
		return self

	k = name

	def val(self, *args, prev=' ', sep=' ') -> CommandBuilder:
		'''
		Append values to command, use format '%s'

		Args:
			args: The values to append
			prev: The prev char
			sep: The sep char between values

		Return:
			CommandBuilder: self

		Alias:
			CommandBuilder.v

		Usage:
			<CommandBuilder>.val('value1', 'value2').name('value3')
		'''
		self.command += prev + sep.join(['%s'] * len(args))
		self.values.extend(args)
		return self

	v = val

	def where(self, name: str, value, oper: str = '=', *, binary: bool = False) -> WhereBuilder:
		'''
		Make where subcommand

		Args:
			name: Match name
			value: Match value
			oper: Match operation
			binary: Case sensitive

		Return:
			WhereBuilder: The builder for build where subcommand

		Alias:
			CommandBuilder.w

		See also:
			WhereBuilder
		'''
		assert not self._where_exists
		self._where_exists = True
		return WhereBuilder(self, name, value, oper)
	w = where

class WhereBuilder:
	'''
	Build `WHERE` subcommand

	Usage:
		<CommandBuilder>.where(key1, value1).done()

	See also:
		CommandBuilder.where
	'''
	def __init__(self, cmd: CommandBuilder, /, name: str, value, oper: str, *, binary: bool = False):
		self._c = cmd
		self._c.append('WHERE')
		if binary:
			self._c.append('BINARY')
		self._f(name, value, oper)

	def done(self) -> CommandBuilder:
		'''
		Unattach the command builder, then return it

		Return:
			CommandBuilder: the command builder attached

		Usage:
			<WhereBuilder>.done()
		'''
		c, self._c = self._c, None
		return c

	d = done

	def _f(self, name: str, value, oper: str):
		self._c.name(name).append(oper).val(value)

	def AND(self, name: str, value, oper: str = '=') -> WhereBuilder:
		self._c.append('AND')
		self._f(name, value, oper)
		return self

	def OR(self, name: str, value, oper: str = '=') -> WhereBuilder:
		self._c.append('OR')
		self._f(name, value, oper)
		return self

class FieldBuilder:
	def __init__(self):
		self._fields = []

	def __str__(self) -> str:
		return '(' + ','.join(self._fields) + ')'

	def __repr__(self):
		return f'<FieldBuilder {self._fields}>'

	def append(self, arg: str) -> FieldBuilder:
		self._fields.append(arg)
		return self

	def field(self, name: str, typ: str, *options: list[str]) -> FieldBuilder:
		return self.append('`{name}` {typ} {option}'.format(name=name, typ=typ, option=' '.join(options)))

	f = field

def create(table: str, /, fields: FieldBuilder = None) -> CommandBuilder:
	'''
	Build `DROP TABLE` sql command

	Args:
		table: The name of the table to create
		fields: The fields of the table to create

	Return:
		CommandBuilder: the command builder to use next

	Usage:
		# Create empty table
		create('example_table')
		# Create table with ENGINE and CHARSET
		create('example_table').append('ENGINE=InnoDB').append('DEFAULT').append('CHARSET=utf8')
	'''
	cmd = CommandBuilder('CREATE').append('TABLE').name(table)
	if fields is not None:
		cmd.append(str(fields))
	return cmd

def drop(table: str, /) -> CommandBuilder:
	'''
	Build `DROP TABLE` sql command

	Args:
		table: The name of the table to drop

	Return:
		CommandBuilder: the command builder to use next

	Usage:
		drop('example_table')
	'''
	return CommandBuilder('DROP').append('TABLE').name(table)

def delete(table: str, /) -> CommandBuilder:
	'''
	Build `DELETE` sql command

	Args:
		table: The name of the target table

	Return:
		CommandBuilder: the command builder to use next

	Usage:
		delete('example_table')
	'''
	return CommandBuilder('DELETE').append('FROM').name(table)

def insert(table: str, /, obj: dict, *, replace: bool = False, ignore: bool = False) -> CommandBuilder:
	'''
	Build `INSERT` sql command

	Args:
		table: The name of the target table
		obj: Data to insert
		replace: replace the row if the primary key already exists, 
		ignore: ignore the row if replace is False and the primary key already exists

	Return:
		CommandBuilder: the command builder to use next

	Usage:
		insert('example_table', dict(key1=value1, key2=value2))
		insert('example_table', dict(key1=value1, key2=value2), replace=True)
		insert('example_table', dict(key1=value1, key2=value2), ignore=True)
	'''
	cmd: CommandBuilder
	if replace:
		cmd = CommandBuilder('REPLACE')
	else:
		cmd = CommandBuilder('INSERT')
		if ignore:
			cmd.append('IGNORE')
	cmd.append('INTO').name(table)
	keys = []
	values = []
	for k, v in obj.items():
		keys.append(k)
		values.append(v)
	cmd.append('(').name(*keys, sep=',').append(')')
	cmd.append('VALUES')
	cmd.append('(').val(*values, sep=',').append(')')
	return cmd

def select(table: str, /, names: list[str] = None) -> CommandBuilder:
	'''
	Build `SELECT` sql command

	Args:
		table: The name of the target table
		names: The keys to select

	Return:
		CommandBuilder: the command builder to use next

	Usage:
		select('example_table') # Select all keys
		select('example_table', ['keys', 'to', 'select']) # Select target keys
	'''
	cmd = CommandBuilder('SELECT')
	if names is None:
		cmd.append('*')
	else:
		cmd.name(*names, sep=',')
	cmd.append('FROM').name(table)
	return cmd

def update(table: str, /, obj: dict) -> CommandBuilder:
	'''
	Build `UPDATE` sql command

	Args:
		table: The name of the target table
		obj: Data to update

	Return:
		CommandBuilder: the command builder to use next

	Usage: update('example_table', dict(key1=value1, key2=value2))
	'''
	cmd = CommandBuilder('UPDATE').name(table)
	first = True
	for k, v in obj.items():
		if first:
			cmd.append('SET')
			first = False
		else:
			cmd.append(',', prev='')
		cmd.name(k).val(v, prev='=')
	return cmd
