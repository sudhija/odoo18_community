/** @odoo-module **/

import { rpc } from "@web/core/network/rpc_service";

console.log("Hotel form loaded");

// Example usage: calling a Python controller or model
async function fetchRoomData(room_id) {
    //const result = await rpc("/hotel/get_room_info", { room_id });
    console.log("Room info:", room_id);
    //return result;
}
