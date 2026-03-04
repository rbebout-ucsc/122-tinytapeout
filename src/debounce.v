
`default_nettype none

module debounce (
    input  wire clk,
    input  wire rst,
    input  wire noisy,
    output reg  clean
);

    reg [15:0] count;
    reg stable_state;

    parameter THRESHOLD = 16'd500;  // 50ms @ 10kHz

    always @(posedge clk) begin
        if (rst) begin
            count <= 0;
            stable_state <= 0;
            clean <= 0;
        end else begin
            if (noisy == stable_state) begin
                count <= 0;
            end else begin
                count <= count + 1;
                if (count >= THRESHOLD) begin
                    stable_state <= noisy;
                    clean <= noisy;
                    count <= 0;
                end
            end
        end
    end
endmodule