# ----------------------------------------------------------------------------
"""
General Utilities
"""
# -----------------------------------------------------------------------------

import os

# -----------------------------------------------------------------------------

bad_argc = 'bad number of arguments\n'
inv_arg = 'invalid argument\n'

limit_64 = (0, 0xffffffffffffffff)
limit_32 = (0, 0xffffffff)

KiB = 1 << 10
MiB = 1 << 20
GiB = 1 << 30

# ----------------------------------------------------------------------------

def memsize(s):
  """return a string for the memory size"""
  if (s >= GiB) and (s & (GiB - 1) == 0):
    return '%dGiB' % (s / GiB)
  if (s >= MiB) and (s & (MiB - 1) == 0):
    return '%dMiB' % (s / MiB)
  if (s >= KiB) and (s & (KiB - 1) == 0):
    return '%dKiB' % (s / KiB)
  return '%dB' % s

# ----------------------------------------------------------------------------
# endian conversions

def identity(x):
  """identity - no changes"""
  return x

def swap16(x):
  """swap endian 16 bits"""
  return ((x & 0xff00) >> 8) | \
         ((x & 0x00ff) << 8)

def btol16(x):
  return swap16(x)

def ltob16(x):
  return swap16(x)

def swap32(x):
  """swap endian 32 bits"""
  return ((x & 0xff000000) >> 24) | \
         ((x & 0x00ff0000) >> 8) | \
         ((x & 0x0000ff00) << 8) | \
         ((x & 0x000000ff) << 24)

def btol32(x):
  return swap32(x)

def ltob32(x):
  return swap32(x)

# -----------------------------------------------------------------------------

def wrong_argc(ui, args, valid):
  """return True if argc is not valid"""
  argc = len(args)
  if argc in valid:
    return False
  else:
    ui.put(bad_argc)
    return True

# -----------------------------------------------------------------------------

def name_arg(ui, arg, names):
  """return a valid name argument - or None"""
  if arg in names:
    return arg
  ui.put(inv_arg)
  return None

# -----------------------------------------------------------------------------

def int_arg(ui, arg, limits, base):
  """convert a number string to an integer - or None"""
  try:
    val = int(arg, base)
  except ValueError:
    ui.put(inv_arg)
    return None
  if (val < limits[0]) or (val > limits[1]):
    ui.put(inv_arg)
    return None
  return val

# ----------------------------------------------------------------------------

def dict_arg(ui, arg, d):
  """argument to value through a dictionary - or None"""
  if d.has_key(arg):
    return d[arg]
  else:
    ui.put(inv_arg)
    return None

# ----------------------------------------------------------------------------

def file_arg(ui, name):
  """return True if the file exists and is non-zero in size"""
  if os.path.isfile(name) == False:
    ui.put('%s does not exist\n' % name)
    return False
  if os.path.getsize(name) == 0:
    ui.put('%s has zero size\n' % name)
    return False
  return True

# ----------------------------------------------------------------------------

def sex_arg(ui, arg, width):
  """sign extend a 32 bit argument to 64 bits"""
  limits = (limit_32, limit_64)[width == 64]
  val = int_arg(ui, arg, limits, 16)
  if val is None:
    return None
  if (len(arg) == 8) and (width == 64):
    if val & (1 << 31):
      val |= (0xffffffff << 32)
  return val

# ----------------------------------------------------------------------------

def align_adr(adr, width):
  """align address to a width bits boundary"""
  return adr & ~((width >> 3) - 1)

def mask_val(val, width):
  """mask a value to width bits"""
  return val & ((1 << width) - 1)

# ----------------------------------------------------------------------------

def nbytes_to_nwords(n, width):
  """how many width-bit words in n bytes?"""
  (mask, shift) = ((3, 2), (7, 3))[width == 64]
  return ((n + mask) & ~mask) >> shift

# -----------------------------------------------------------------------------

def mem_region_args(ui, args, device, default_size = None):
  """memory region arguments: return (adr, size) or None"""
  adr = None
  size = None

  if wrong_argc(ui, args, (1, 2)):
    return None

  if len(args) >= 1:
    if device.peripherals.has_key(args[0]):
      # args[0] is a peripheral name
      p = device.peripherals[args[0]]
      adr = p.address
      size = p.size
    else:
      # args[0] is an address
      adr = sex_arg(ui, args[0], 32)
      if adr is None:
        return None

  if len(args) >= 2:
    # do we have a length?
    size = int_arg(ui, args[1], (1, 0xffffffff), 16)
    if size is None:
      return None

  if size is None:
    size = default_size

  if size is None:
    ui.put('bad size')
    return None

  return (adr, size)

# -----------------------------------------------------------------------------

def mem_file_args(ui, args, device):
  """memory/file arguments: return (adr, n, name) or None"""

  adr = None
  n = None
  name = 'mem.bin'

  if wrong_argc(ui, args, (1, 2, 3)):
    return None

  if len(args) >= 1:
    if device.peripherals.has_key(args[0]):
      # args[0] is a peripheral name
      p = device.peripherals[args[0]]
      adr = p.address
      n = p.size
    else:
      # args[0] is an address
      adr = sex_arg(ui, args[0], 32)
      if adr is None:
        return None

  if len(args) >= 2:
    # do we have a length or a filename?
    try:
      int(args[1], 16)
      n = int_arg(ui, args[1], (1, 0xffffffff), 16)
    except ValueError:
      name = args[1]

  if n is None:
    ui.put('bad length')
    return None

  if len(args) >= 3:
    name = args[2]

  return (adr, n, name)

# ----------------------------------------------------------------------------

def parameter_str(parms):
  """return a string with parameters and values"""
  return '\n'.join(['%-23s: %s' % x for x in parms])

# ----------------------------------------------------------------------------
# bit field manipulation

def maskshift(field):
  """return a mask and shift defined by field"""
  if len(field) == 1:
    return (1 << field[0], field[0])
  else:
    return (((1 << (field[0] - field[1] + 1)) - 1) << field[1], field[1])

def bits(val, field):
  """return the bits (masked and shifted) from the value"""
  (mask, shift) = maskshift(field)
  return (val & mask) >> shift

def masked(val, field):
  """return the bits (masked only) from the value"""
  return val & maskshift(field)[0]

def ls_bit(x):
  """return the index of the least significant 1 bit"""
  if x == 0:
    return None
  n = 0
  while x & (1 << n) == 0:
    n += 1
  return n

# ----------------------------------------------------------------------------

def format_dec(val):
  return '%d' % val

def format_hex32(val):
  return '%08x' % val

def bitfield_v(val, fields, col=15):
  """
  return a string of bit field components formatted vertically
  val: the value to be split into bit fields
  fields: a tuple of (name, output_function, (bit_hi, bit_lo)) tuples
  """
  fmt = '%%-%ds: %%s' % col
  s = []
  for (name, func, field) in fields:
    s.append(fmt % (name, func(bits(val, field))))
  return '\n'.join(s)

def bitfield_h(val, fields):
  """
  return a string of bit field components formatted horizontally
  val: the value to be split into bit fields
  fields: a tuple of (name, output_function, (bit_hi, bit_lo)) tuples
  """
  l = []
  for (name, func, field) in fields:
    if func is None:
      if bits(val, field) != 0:
        l.append('%s' % name)
    elif name is None:
      s = func(bits(val, field))
      if s:
        l.append(s)
    else:
      l.append(('%s(%s)' % (name, func(bits(val, field)))))
  return ' '.join(l)

# -----------------------------------------------------------------------------

def format_bit(x, c):
  if x == 0:
    return '.'
  elif x == 1:
    return c
  return ' '

# -----------------------------------------------------------------------------

def rm_prefix(names, prefix_set):
  if prefix_set is None:
    return
  # find the longest matching prefix for all names
  n = 0
  for p in prefix_set:
    match = True
    for x in names:
      if not x.startswith(p):
        match = False
        break
    if match and len(p) > n:
      n = len(p)
  # remove the prefix
  if n:
    #print('removing prefix %s' % names[0][:n])
    for i in xrange(len(names)):
      names[i] = names[i][n:]

def rm_suffix(names, suffix_set):
  if suffix_set is None:
    return
  # find the longest matching suffix for all names
  n = 0
  for s in suffix_set:
    match = True
    for x in names:
      if not x.endswith(s):
        match = False
        break
    if match and len(s) > n:
      n = len(s)
  # remove the suffix
  if n:
    #print('removing suffix %s' % names[0][-n:])
    for i in xrange(len(names)):
      names[i] = names[i][:-n]

# -----------------------------------------------------------------------------

def display_cols(clist, csize = None):
  """
    return a string for a list of columns
    each element in clist is [col0_str, col1_str, col2_str, ...]
    csize is a list of column width minimums
  """
  # how many columns?
  ncols = len(clist[0])
  # make sure we have a well formed csize
  if csize is None:
    csize = [0,] * ncols
  else:
    assert len(csize) == ncols
  # convert any "None" items to ''
  for l in clist:
    assert len(l) == ncols
    for i in range(ncols):
      if l[i] is None:
        l[i] = ''
  # additional column margin
  cmargin = 1
  # go through the strings and bump up csize widths if required
  for l in clist:
    for i in range(ncols):
      if csize[i] <= len(l[i]):
        csize[i] = len(l[i]) + cmargin
  # build the format string
  fmt = []
  for n in csize:
    fmt.append('%%-%ds' % n)
  fmt = ''.join(fmt)
  # generate the string
  s = [(fmt % tuple(l)) for l in clist]
  return '\n'.join(s)

# -----------------------------------------------------------------------------

class progress:
  """percent complete and activity indication"""

  def __init__(self, ui, div, nmax):
    """
    progress indicator
    div = slash speed, larger is slower
    nmax = maximum value, 100%
    """
    self.ui = ui
    self.nmax = nmax
    self.progress = ''
    self.div = div
    self.mask = (1 << div) - 1

  def erase(self):
    """erase the progress indication"""
    n = len(self.progress)
    self.ui.put(''.join(['\b' * n, ' ' * n, '\b' * n]))

  def update(self, n):
    """update the progress indication"""
    if n & self.mask == 0:
      self.erase()
      istr = '-\\|/'[(n >> self.div) & 3]
      pstr = '%d%% ' % ((100 * n) / self.nmax)
      self.progress = ''.join([pstr, istr])
      self.ui.put(self.progress)

# -----------------------------------------------------------------------------
