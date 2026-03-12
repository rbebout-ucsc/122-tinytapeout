`default_nettype none
module tt_um_d20_roller_rbebout(
    input  wire [7:0] ui_in,
    output wire [7:0] uo_out,
    input  wire [7:0] uio_in,
    output wire [7:0] uio_out,
    output wire [7:0] uio_oe,
    input  wire       ena,
    input  wire       clk,
    input  wire       rst_n
);
    wire rst   = ui_in[0];
    wire start = ui_in[1];
    wire start_stable;
    wire reset_stable;
    wire [4:0] final_value;
    wire active;

    debouncer #() db_rst (
        .clk(clk), .rst(1'b0),
        .btn(rst), .stable_out(reset_stable)
    );
    debouncer #() db_btn (
        .clk(clk), .rst(1'b0),
        .btn(start), .stable_out(start_stable)
    );

    d20_core core (
        .clk(clk),
        .rst(reset_stable),
        .start(start_stable),
        .value(final_value),
        .active(active)
    );

    wire [6:0] seg_wire;
    wire [1:0] digits_wire;

    display_driver disp (
        .clk(clk),
        .rst(reset_stable),
        .active(active),
        .value(final_value),
        .seg(seg_wire),
        .digits(digits_wire)
    );

    assign uo_out[0] = seg_wire[0];
    assign uo_out[1] = seg_wire[1];
    assign uo_out[2] = seg_wire[2];
    assign uo_out[3] = seg_wire[3];
    assign uo_out[4] = seg_wire[4];
    assign uo_out[5] = seg_wire[5];
    assign uo_out[6] = seg_wire[6];
    assign uo_out[7] = 1'b0;

    assign uio_out[0] = digits_wire[0];
    assign uio_out[1] = digits_wire[1];
    assign uio_out[2] = start_stable;
    assign uio_out[3] = reset_stable;
    assign uio_out[7:4] = 4'b0;

    assign uio_oe = 8'b000001111;

    wire _unused = &{ena, ui_in[7:2], uio_in, rst_n, 1'b0};
endmodule