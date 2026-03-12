`default_nettype none

module debouncer (
    input  wire clk,
    input  wire rst,
    input  wire btn,
    output wire stable_out
);
    parameter DEBOUNCE_CYCLES = 500;
    parameter CTR_BITS = 9;

    // 2-FF synchroniser
    reg sync_ff1, sync_ff2;
    always @(posedge clk) begin
        sync_ff1 <= btn;
        sync_ff2 <= sync_ff1;
    end

    reg [CTR_BITS-1:0] counter;
    reg stable;

    initial begin
        counter = 0;
        stable  = 0;
    end

    always @(posedge clk) begin
        if (rst) begin
            counter <= 0;
            stable  <= 1'b0;
        end else begin
            if (sync_ff2 == stable) begin
                counter <= 0;
            end else if (counter == DEBOUNCE_CYCLES - 1) begin
                counter <= 0;
                stable  <= sync_ff2;
            end else begin
                counter <= counter + 1'b1;
            end
        end
    end

    assign stable_out = stable;

endmodule