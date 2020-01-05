// How to restart always trips me up
// - Assume that restart must come in after we are done?
module count_every_ii_clks(input clk, input rst, input start, output out);

  parameter N = 2;
  parameter II = 1;

  // Start with the simplest thing: Assume N == 1, II == 1
  //
  // Impl: 

  reg last_start;


  //reg [31:0] current_cnt;
  //reg [31:0] delay;
  //reg started_in_prior_cycle;
  //reg done;

  //wire active;

  //assign active = start | started_in_prior_cycle;

  always @(posedge clk) begin
    if (rst) begin
      last_start <= 0;
    end else begin
      last_start <= start;
    end
    //if (rst) begin
      //started_in_prior_cycle <= 0;
      //current_cnt <= 0;
      //delay <= II;
      //done <= 0;
    //end else begin
      //if (start) begin
        //started_in_prior_cycle <= 1;
        //current_cnt <= 0;
      //end

      //if (active) begin:
        //delay <= delay == 0 ? II : delay - 1;
      //end
    //end
  end

  assign out = start | last_start;
  
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

// Self transition is: II clks since last signal and
// condition_at_last_signal(happening, !x_at_trip_count)
module reg_1(input clk, input rst, input en, input d, output q);
endmodule
