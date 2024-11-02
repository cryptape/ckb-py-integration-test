local callee_code = [[
local m = arg[2] .. arg[3]
local inherited_fds, err = ckb.inherited_fds()
local n, err = ckb.write(inherited_fds[1], m)
ckb.close(inherited_fds[1])
assert(n == 10)
local pid = ckb.process_id()
assert(pid >= 1)
]]

local fds, err = ckb.pipe()
assert(err == nil)
local buf,error = ckb.load_block_extension(0, ckb.SOURCE_INPUT)
assert(not error)
assert(#buf == 32)

