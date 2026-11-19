from moomoo import OpenQuoteContext

ctx = OpenQuoteContext(host="127.0.0.1", port=11111)
print(ctx.get_global_state())
ctx.close()