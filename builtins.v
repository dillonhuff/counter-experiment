module single_port_sram(input clk,
  input rst,
  input [$clog2(DEPTH) - 1 : 0] addr,
  input ren,
  input wen,
  output reg [WIDTH - 1 : 0] q,
  input [WIDTH - 1 : 0] d);

  parameter WIDTH = 32;
  parameter DEPTH = 32;

  reg [WIDTH - 1 : 0] data [DEPTH -1 : 0];

  reg [$clog2(DEPTH) - 1 : 0] addr_reg;
  reg [WIDTH - 1 : 0] data_reg;
  reg do_read;
  reg do_write;

  always @(posedge clk) begin
    if (ren & wen) begin
      $display("ERROR: Reading and writing at the same time!");
      $finish(1);
    end

    if (rst) begin
      do_read <= 0;
      do_write <= 0;
    end else begin

      if (wen) begin
        do_write <= 1;
        data_reg <= d;
        addr_reg <= addr;
      end else begin
        do_write <= 0;
      end

      if (ren) begin
        do_read <= 1;
        data_reg <= data[addr];
      end else begin
        do_read <= 0;
      end

    end
  end

  always @(*) begin
    if (do_read) begin
      q = data_reg;
    end else begin
      // Dummy value to make errors more obvious
      q = 189;
    end
  end
  
  always @(*) begin
    if (do_write) begin
      data[addr_reg] = data_reg;
    end 
  end

endmodule

module shift_register #(
    parameter L = 1, // Number of stages (1 = this is a simple FF)
    parameter W = 1// Width of Serial_in / Serial_out
) (
    input clk, rst, en,
    input [W-1:0] Serial_in,
    output [W-1:0] Serial_out
);
    reg [L*W-1:0] shreg;

    always @(posedge clk) begin
      if (rst) begin
        shreg <= 0;
      end else if (en) begin
        //shreg <= {shreg, Serial_in};
        //shreg <= {shreg[L*W - 1: 0], Serial_in};
        // TODO: Generalize for many dims
        shreg <= Serial_in;
      end
    end

    assign Serial_out = en & shreg[L*W-1:(L-1)*W];
endmodule

// Note that when clear is high the counter is cleared on the next cycle
module counter(input clk, input rst, input clear, input en, output [31:0] out);

  parameter MIN = 0;
  parameter MAX = 1;

  reg [31:0] out_data;

  always @(posedge clk) begin
    if (rst) begin
      out_data <= MIN;
    end else if (clear) begin
      out_data <= MIN;
    end else if (en && out_data < MAX) begin
      out_data <= out_data + 1;
    end

  end

  assign out = out_data;

endmodule

// Assumed signal order:
// en < clear < rst
module m_counter(input clk, input rst, input clear, input en, output [31:0] out);

  parameter MIN = 0;
  parameter MAX = 1;

  reg [31:0] out_data;
  reg [31:0] last_clk_state;

  always @(*) begin
    if (clear) begin
      $display("clearing");
      out_data = MIN;
    end else if (en && last_clk_state < MAX) begin
      out_data = last_clk_state + 1;
    end else begin
      out_data = last_clk_state;
    end
  end

  always @(posedge clk) begin
    if (rst) begin
      $display("reseting");
      last_clk_state <= MIN;
    end else begin
      last_clk_state <= out_data;
    end
  end

  assign out = out_data;

endmodule

module counter_continue(input clk, input rst, input clear, output [31:0] out);

  parameter MIN = 0;
  parameter MAX = 1;

  counter #(.MIN(MIN), .MAX(MAX)) c(.clk(clk), .rst(rst), .clear(clear), .en(1'b1), .out(out));

endmodule

module count_every_ii_clks(input clk, input rst, input start, output out);

  parameter N = 2;
  parameter II = 1;

  wire [31:0] cnt_out;
  reg started_in_past_cycle;
  
  m_counter #(.MIN(0), .MAX(N*II)) cnt_later(.clk(clk), .rst(rst), .clear(start), .en(1'b1), .out(cnt_out));
  wire active = start | (started_in_past_cycle & (cnt_out / II) < N & (cnt_out % II == 0));

  always @(posedge clk) begin
    $display("cnt out = %d", cnt_out);

    if (rst) begin
      started_in_past_cycle <= 0;
    end else begin
      if (start) begin
        started_in_past_cycle <= 1;
      end
    end
  end

  assign out = active;
  
endmodule

module count_every_ii_signals(input clk, input rst, input start, input signal, output out);

  parameter N = 2;
  parameter II = 1;

  wire [31:0] cnt_out;
  reg started_in_past_cycle;
  
  m_counter #(.MIN(0), .MAX(N*II)) cnt_later(.clk(clk), .rst(rst), .clear(start), .en(signal), .out(cnt_out));
  wire active = start | (signal & (started_in_past_cycle & (cnt_out / II) < N & (cnt_out % II == 0)));

  always @(posedge clk) begin
    $display("cnt out = %d", cnt_out);

    if (rst) begin
      started_in_past_cycle <= 0;
    end else begin
      if (start) begin
        started_in_past_cycle <= 1;
      end
    end
  end

  assign out = active;
  
endmodule
// Counts number of clock edges since arrival of signal, assuming the clock is
// after the signal
module clks_since_signal(input clk, input rst, input signal, output [31:0] num, output no_signal_yet);

  reg [31:0] clks_elapsed_since_last_signal;
  reg signal_seen;
  
  assign num = clks_elapsed_since_last_signal;
  assign no_signal_yet = !signal_seen;
  
  //assign num = signal ? 0 : clks_elapsed_since_last_signal;
  //assign no_signal_yet = signal ? 0 : signal_seen;

  always @(posedge clk) begin
    if (rst) begin
      clks_elapsed_since_last_signal <= 0;
      signal_seen <= 0;
    end else begin
      if (signal) begin
        clks_elapsed_since_last_signal <= 1;
        signal_seen <= 1;
      end else begin
        clks_elapsed_since_last_signal <=
          clks_elapsed_since_last_signal + 1;
      end
    end
  end

endmodule

module signal_seen_first(input clk, input rst, input signal, output seen);

  reg seen_in_past_cycle;

  assign seen = signal & !seen_in_past_cycle;

  always @(posedge clk) begin
    if (rst) begin
      seen_in_past_cycle <= 0;
    end else if (signal) begin
      seen_in_past_cycle <= 1;
    end
  end
endmodule

module n_clks_since_signal(input clk, input rst, input signal, output out);

  parameter N = 1;

  wire [31:0] num_clks;
  wire no_signal_yet;

  clks_since_signal sig_cntr(.clk(clk), .rst(rst), .signal(signal), .no_signal_yet(no_signal_yet), .num(num_clks));

  assign out = !no_signal_yet & (num_clks == N);

endmodule

module condition_at_last_signal(input clk, input rst, input signal, input condition, output out, output no_signal_yet);

  reg signal_seen;
  reg condition_value_at_last_signal;
  assign no_signal_yet = signal ? 0 : !signal_seen;
  assign out = signal ? condition : condition_value_at_last_signal;

  always @(posedge clk) begin
    if (rst) begin
      signal_seen <= 0;
    end else begin
      if (signal) begin
        signal_seen <= 1;
        condition_value_at_last_signal <= condition;
      end else begin
      end
    end
  end
  
endmodule

module register_s(input clk, input rst, input en, input [WIDTH - 1 :0] d, output [WIDTH - 1:0] q);

  parameter WIDTH;

  reg [WIDTH - 1 :0] d_data;
  always @(posedge clk) begin
    if (rst) begin
      d_data <= 0;
    end else begin
      if (en) begin
        d_data <= d;
      end
    end
  end

  assign q = d_data;

endmodule
module register_32(input clk, input rst, input en, input [31:0] d, output [31:0] q);

  reg [31:0] d_data;
  always @(posedge clk) begin
    if (rst) begin
      d_data <= 0;
    end else begin
      if (en) begin
        d_data <= d;
      end
    end
  end

  assign q = d_data;

endmodule

// Self transition is: II clks since last signal and
// condition_at_last_signal(happening, !x_at_trip_count)
module reg_1(input clk, input rst, input en, input d, output q);
endmodule

module aggregator(input clk,
  input rst,
  input en,
  input [WIDTH - 1 : 0] in,
  output [N_OUTS*WIDTH - 1 : 0] out);

  parameter WIDTH = 1;
  parameter N_OUTS = 1;
  
  reg do_write;
  reg [WIDTH - 1 : 0] data [N_OUTS - 1 : 0];
  wire [31:0] next_write_addr;
  wire wrap_addr = do_write & (next_write_addr == (N_OUTS - 1));

  always @(posedge clk) begin
    if (rst) begin
      do_write <= 0;
    end else begin
      if (en) begin
        do_write <= 1;
      end else begin
        do_write <= 0;
      end
    end
  end

  counter #(MIN(0), .MAX(N_OUTS - 1)) addr(.clk(clk), .rst(rst), .clear(wrap_addr), .en(en), .out(next_write_addr));

  assign out = data;

endmodule

