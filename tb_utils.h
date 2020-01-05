#pragma once

#define set_sig(p, sig, val) p.sig = (val); p.eval();
#define pos(p, sig) set_sig(p, sig, 0); set_sig(p, sig, 1);
#define reset(p) set_sig(p, rst, 1); pos(p, clk); set_sig(p, rst, 0); set_sig(p, clk, 0);

