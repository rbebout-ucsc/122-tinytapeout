
`default_nettype none

module d20_core (
    input  wire clk,
    input  wire rst,        // use reset_pulse here
    input  wire start,      // 1-cycle pulse from edge_detect
    output reg  [4:0] value,
    output reg  active
);

    //--------------------------------------------------
    // Control State (ONLY handles toggle)
    //--------------------------------------------------
    reg rolling;

    always @(posedge clk) begin
        if (rst)
            rolling <= 1'b0;
        else if (start)
            rolling <= ~rolling;
    end


    //--------------------------------------------------
    // Datapath (counter + divider)
    //--------------------------------------------------
    reg [9:0] div;

    always @(posedge clk) begin
        if (rst) begin
            div    <= 10'd0;
            value  <= 5'd1;
            active <= 1'b0;
        end
        else begin

            // Once we roll once, display stays active
            if (rolling)
                active <= 1'b1;

            if (rolling) begin
                if (div == 10'd500) begin
                    div <= 10'd0;

                    if (value == 5'd20)
                        value <= 5'd1;
                    else
                        value <= value + 5'd1;

                end else begin
                    div <= div + 10'd1;
                end
            end
            else begin
                div <= 10'd0;   // reset divider when stopped
            end
        end
    end

endmodule