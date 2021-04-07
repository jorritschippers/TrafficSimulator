#include <iostream>

#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>
#include <nlohmann/json.hpp>

#include <windows.h>


using namespace std;
using json = nlohmann::json;
using jsonorder = nlohmann::ordered_json;

typedef websocketpp::server<websocketpp::config::asio> server;
string ip = "192.168.178.66";

server print_server;
jsonorder verkeersoverzicht;
server::connection_ptr con;


void init_verkeersoverzicht() {
    verkeersoverzicht = {
        {{"id",1 },{"crosses",{2,3,4}},{"clearing_time",3},{"state","red"},{"vehicles_waiting",TRUE},{"vehicles_coming",FALSE}},
        {{"id",2 },{"crosses",{1,5,6}},{"clearing_time",2},{"state","green"},{"vehicles_waiting",FALSE},{"vehicles_coming",FALSE}}
    };
}

void init_clientconnection(websocketpp::connection_hdl hdl) {
    con = print_server.get_con_from_hdl(hdl);
}

void change_state(const int& id, const std::string& newState)
{
    for (auto it = verkeersoverzicht.begin(); it != verkeersoverzicht.end(); ++it) {
        if(it.value()["id"] == id){
            it.value()["state"] = newState;
            con->send("Stoplicht " + to_string(id) + " staat nu op " + newState);
        }
    }
}



void on_message(websocketpp::connection_hdl hdl, server::message_ptr msg) {
    jsonorder ontvangen = jsonorder::parse(msg->get_payload());
    string msgtype = ontvangen["msg_type"];

    if (msgtype == "notify_state_change") {

    }

    if (msgtype == "perform_state_change") {
        for (const auto& item : ontvangen["data"].items()) {
            change_state(item.value()["id"], item.value()["state"]);
        } 
    }
}

void on_connection(websocketpp::connection_hdl hdl) {
    init_verkeersoverzicht();
    init_clientconnection(hdl);

    jsonorder state = {
    {"msg_type","notify_state_change"},
    {"data", verkeersoverzicht} };
    con->send(state.dump());
}


int main() {
    
    print_server.set_message_handler(&on_message);
    print_server.set_open_handler(&on_connection);
    print_server.set_access_channels(websocketpp::log::alevel::message_payload);
    print_server.set_error_channels(websocketpp::log::elevel::all);

    print_server.init_asio();

    // Listen on port.
    int port = 6969;
    try {
        print_server.listen(port);
    }
    catch (websocketpp::exception const& e) {
        // Websocket exception on listen. Get char string via e.what().
        cout << e.what() << endl;
    }


    print_server.start_accept();
    std::cout << "Server is running" << std::endl;

    print_server.run();

    std::cout << "test" << std::endl;
}



