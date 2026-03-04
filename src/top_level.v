    
`default_nettype none

module tt_um_d20_roller_rbebout(
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset

);

    wire rst   = ui_in[0];
    wire start = ui_in[1];

    wire start_clean;
    wire start_pulse;
    wire reset_pulse;
    wire [4:0] roll_value;
    wire [4:0] final_value;
    wire active;

    wire [3:0] tens;
    wire [3:0] ones;


    edge_detect ed_reset (
    .clk(clk),
    .rst(1'b0),
    .signal_in(rst),
    .rising_edge(reset_pulse)
);

    button_toggle btn_ctrl (
    .clk(clk),
    .rst(rst),
    .btn(start),
    .pulse(start_pulse)
);

    // core roller
    d20_core core (
        .clk(clk),
        .rst(reset_pulse),
        .start(start_pulse),
        .value(final_value),
        .active(active)
    );

    // digit split
    digit_split split (
        .clk(clk),
        .value(final_value),
        .active(active),
        .tens(tens),
        .ones(ones)
    );
    
    assign uio_oe 8'b11000000;
    // display
    display_driver disp (
        .clk(clk),
        .rst(reset_pulse),
        .active(active),
        .tens(tens),
        .ones(ones),
        .seg({uo_out[0], uo_out[1], uo_out[2], uo_out[3], uo_out[4], uo_out[5], uo_out[6]}),
        .DIG1(uio_out[0]),
        .DIG2(uio_out[1])
    );

wire _unused = &{ena, ui_in[7:2], uio_in, uio_out[7:2], uo_out[7], rst_n, 1'b0};

endmodule