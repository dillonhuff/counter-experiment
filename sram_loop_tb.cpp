
#include "verilated.h"

#include "Vsram_loop.h"

#include <iostream>
#include "tb_utils.h"

using namespace std;

void check_total_output() {

  cout << "Starting total output sram vectorize" << endl;
  Vsram_loop p;
  p.rst = 0;
  p.clk = 0;
  p.en = 0;
  reset(p);

  assert(p.valid == 0);

  pos(p, clk);

  assert(p.valid == 0);

  set_sig(p, en, 1);
  set_sig(p, in, 1236);
  set_sig(p, in_addr, 5);

  // Commit the valid, internally the write to the sram should start
  pos(p, clk);
 
  // Dont add any new inputs
  set_sig(p, en, 0);
  
  assert(p.valid == 0);
 
  // finish write and start read
  pos(p, clk);


  cout << "valid = " << p.valid << endl;
  cout << "out   = " << p.out << endl;
  assert(p.valid == 1);
  assert(p.out == 1236);

  // finish read
  pos(p, clk);

  assert(p.valid == 0);

  cout << "total output test passed" << endl;
}

int main() {
  check_total_output();
  return 0;
}

