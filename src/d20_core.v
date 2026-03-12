
`default_nettype none

module d20_core (
    input  wire clk,
    input  wire rst,
    input  wire start,
    output reg  [4:0] value,
    output reg  active
);
    reg [4:0] lfsr;
    parameter BLANK_CYCLES = 25000;
    parameter BLANK_BITS   = 15;
    reg [BLANK_BITS-1:0] blank_ctr;
    reg                  blanking;
    reg start_prev;
    wire start_rise = start & ~start_prev;

    initial begin
        lfsr      = 5'b00001;
        value     = 0;
        active    = 0;
        blanking  = 0;
        blank_ctr = 0;
        start_prev = 0;
    end

    always @(posedge clk) begin
        if (rst) begin
            lfsr       <= 5'b00001;
            value      <= 5'd0;
            active     <= 1'b0;
            blanking   <= 1'b0;
            blank_ctr  <= 0;
            start_prev <= 1'b0;
        end else begin
            start_prev <= start;

            if (lfsr == 5'b0)
                lfsr <= 5'b00001;
            else
                lfsr <= {lfsr[3:0], lfsr[4] ^ lfsr[2]};

            if (blanking) begin
                if (blank_ctr == BLANK_CYCLES - 1) begin
                    blanking  <= 1'b0;
                    blank_ctr <= 0;
                    active    <= 1'b1;
                end else begin
                    blank_ctr <= blank_ctr + 1'b1;
                end
            end

            if (start_rise) begin
                if (lfsr >= 5'd21)
                    value <= lfsr - 5'd20;
                else
                    value <= lfsr;
                active    <= 1'b0;
                blanking  <= 1'b1;
                blank_ctr <= 0;
            end
        end
    end
endmodule