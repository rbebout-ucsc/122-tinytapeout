
`default_nettype none

module button_toggle (
    input  wire clk,
    input  wire rst,
    input  wire btn,        // raw button
    output reg  pulse       // one pulse per press
);

    reg sync0, sync1;
    reg pressed;

    // 2FF synchronizer
    always @(posedge clk) begin
        sync0 <= btn;
        sync1 <= sync0;
    end

    always @(posedge clk) begin
        if (rst) begin
            pressed <= 0;
            pulse   <= 0;
        end else begin
            pulse <= 0;

            // rising edge and not already pressed
            if (sync1 && !pressed) begin
                pulse   <= 1;
                pressed <= 1;
            end

            // re-arm on release
            if (!sync1)
                pressed <= 0;
        end
    end

endmodule