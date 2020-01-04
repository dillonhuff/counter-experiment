module clks_since_signal(input clk, input rst, input signal, output [31:0] num, output no_signal_yet);

  reg [31:0] clks_elapsed_since_last_signal;
  reg signal_seen;
  assign num = signal ? 0 : clks_elapsed_since_last_signal;
  assign no_signal_yet = signal ? 0 : signal_seen;

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
  assign no_signal_yet = signal ? 0 : signal_seen;
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

// Self transition is: II clks since last signal and
// condition_at_last_signal(happening, !x_at_trip_count)
module reg_1(input clk, input rst, input en, input d, output q);
endmodule
