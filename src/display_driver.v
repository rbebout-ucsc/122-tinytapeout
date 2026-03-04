
`default_nettype none

module display_driver (
    input  wire clk,
    input  wire rst,
    input  wire active,
    input  wire [3:0] tens,
    input  wire [3:0] ones,
    output reg  [6:0] seg,
    output reg  DIG1,
    output reg  DIG2
);

    reg [8:0] refresh;  // 10kHz → ~20Hz per digit
    reg digit;

    function [6:0] decode;
        input [3:0] val;
        begin
            case(val)
                4'd0: decode = 7'b0000001;
                4'd1: decode = 7'b1001111;
                4'd2: decode = 7'b0010010;
                4'd3: decode = 7'b0000110;
                4'd4: decode = 7'b1001100;
                4'd5: decode = 7'b0100100;
                4'd6: decode = 7'b0100000;
                4'd7: decode = 7'b0001111;
                4'd8: decode = 7'b0000000;
                4'd9: decode = 7'b0000100;
                default: decode = 7'b1111111; // blank
            endcase
        end
    endfunction

    always @(posedge clk) begin
        if (rst) begin
            refresh <= 0;
            digit <= 0;
            DIG1 <= 1;
            DIG2 <= 1;
            seg <= 7'b1111111;
        end else begin

            refresh <= refresh + 1;

            if (refresh == 100) begin
                refresh <= 0;
                digit <= ~digit;
            end

            DIG1 <= 1;
            DIG2 <= 1;

            if (!active) begin
                seg <= 7'b1111111;
            end else if (digit == 0) begin
                seg <= decode(ones);
                DIG1 <= 0;
            end else begin
                seg <= decode(tens);
                DIG2 <= 0;
            end
        end
    end
endmodule