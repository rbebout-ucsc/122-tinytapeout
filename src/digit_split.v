
`default_nettype none

module digit_split (
    input  wire [4:0] value,
    input  wire active,
    output reg  [3:0] tens,
    output reg  [3:0] ones
);

    always @(*) begin
        if (!active) begin
            tens = 4'hF;  // blank
            ones = 4'hF;
        end
        else if (value <= 9) begin
            tens = 4'hF;  // BLANK instead of 0
            ones = value;
        end
        else begin
            tens = value / 10;
            ones = value % 10;
        end
    end
endmodule