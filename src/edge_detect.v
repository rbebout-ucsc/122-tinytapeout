
`default_nettype none

module edge_detect (
    input  wire clk,
    input  wire rst,
    input  wire signal_in,   // debounced button
    output wire rising_edge  // 1-cycle pulse
);

    reg sync_0;
    reg sync_1;
    reg prev;

    // 2-flip-flop synchronizer
    always @(posedge clk) begin
        if (rst) begin
            sync_0 <= 0;
            sync_1 <= 0;
            prev   <= 0;
        end else begin
            sync_0 <= signal_in;
            sync_1 <= sync_0;
            prev   <= sync_1;
        end
    end

    assign rising_edge = sync_1 & ~prev;

endmodule