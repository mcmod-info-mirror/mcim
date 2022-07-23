
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
	def __init__(self, cmd: str, /):
		self.command = cmd
		self.values = []
		self._where_exists = False

	def __str__(self):
		return self.command

	def __repr__(self):
		return f'<CommandBuilder {self.command}>'

	def append(self, arg, prev=' ') -> CommandBuilder:
		self.command += prev + arg
		return self

	def name(self, *args, prev=' ', sep=' ') -> CommandBuilder:
		self.command += prev + sep.join(f'`{k}`' for k in args)
		return self

	k = name

	def val(self, *args, prev=' ', sep=' ') -> CommandBuilder:
		fmts = []
		for v in args:
			if isinstance(v, (str)):
				fmts.append('%s')
			elif isinstance(v, (int, float)):
				fmts.append('%d')
			else:
				fmts.append('%s')
		self.values.extend(args)
		self.command += prev + sep.join(fmts)
		return self

	v = val

	def where(self, name: str, value, oper: str = '=', *, binary: bool = False) -> WhereBuilder:
		assert not self._where_exists
		self._where_exists = True
		return WhereBuilder(self, name, value, oper)

	w = where

class WhereBuilder:
	def __init__(self, cmd: CommandBuilder, /, name: str, value, oper: str, *, binary: bool = False):
		self._c = cmd
		self._c.append('WHERE')
		if binary:
			self._c.append('BINARY')
		self._f(name, value, oper)

	def done(self) -> CommandBuilder:
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

def create(name: str, /, fields: FieldBuilder = None) -> CommandBuilder:
	cmd = CommandBuilder('CREATE').append('TABLE').name(table)
	if fields is not None:
		cmd.append(str(fields))
	return cmd

def drop(name: str, /) -> CommandBuilder:
	return CommandBuilder('DROP').append('TABLE').name(table)

def delete(table: str, /) -> CommandBuilder:
	return CommandBuilder('DELETE').append('FROM').name(table)

def insert(table: str, /, obj: dict, *, replace: bool = False, ignore: bool = False) -> CommandBuilder:
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
	cmd.name(*keys, sep=',')
	cmd.append('VALUES')
	cmd.val(*values, sep=',')
	return cmd

def select(table: str, /, names: list[str] = None) -> CommandBuilder:
	cmd = CommandBuilder('SELECT')
	if names is None:
		cmd.append('*')
	else:
		cmd.name(*names)
	cmd.append('FROM').name(table)
	return cmd

def update(table: str, /, kwargs: dict) -> CommandBuilder:
	cmd = CommandBuilder('UPDATE').name(table)
	first = False
	for k, v in obj.items():
		if first:
			cmd.append('SET')
			first = False
		else:
			cmd.append(',', prev='')
		cmd.name(k).val(v, prev='=')
	return cmd
