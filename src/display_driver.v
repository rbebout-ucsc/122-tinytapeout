
`default_nettype none

module display_driver (
    input  wire clk,
    input  wire rst,
    input  wire active,
    input  wire [4:0] value,
    output reg  [6:0] seg,
    output reg  [1:0] digits
);

    function [6:0] decode;
        input [3:0] val;
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
            default: decode = 7'b1111111;
        endcase
    endfunction

    reg active_digit;

    initial begin
        active_digit = 0;
        digits       = 2'b01;
        seg          = 7'b1111111;
    end


    // Simple arithmetic replaces get_ones/get_tens functions
    wire [3:0] ones = (value == 5'd20) ? 4'd0 : (value % 10);
    wire [3:0] tens = (value >= 5'd20) ? 4'd2 : (value >= 5'd10) ? 4'd1 : 4'hF;

    always @(posedge clk) begin
        if (rst) begin
            active_digit <= 1'b0;
            digits       <= 2'b01;
            seg          <= 7'b1111111;
        end else begin
            active_digit <= ~active_digit;
            if (active_digit == 1'b0) begin
                digits <= 2'b01;
                seg    <= active ? decode(ones) : 7'b1111111;
            end else begin
                digits <= 2'b10;
                seg    <= active ? decode(tens) : 7'b1111111;
            end
        end
    end

endmodule