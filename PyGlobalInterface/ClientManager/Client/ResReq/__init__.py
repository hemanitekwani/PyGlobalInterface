from PyGlobalInterface.log import configure_logger

logger = configure_logger(__name__)
class Events:
    AWK_CLIENT_RECV = "AWK_CLIENT_RECV"
    
    AWK_CLIENT_VERIFY = "AWK_CLIENT_VERIFY"
    AWK_CLIENT_NOT_VERIFY_DUE_TO_CHECK = "AWK_CLIENT_NOT_VERIFY_DUE_CHECK"
    AWK_CLIENT_NOT_VERIFY_DUE_TO_LIMIT = "AWK_CLIENT_NOT_VERIFY_DUE_TO_LIMIT"


    AWK_CLIENT_FUNCTION_CALL = "AWK_CLIENT_FUNCTION_CALL"
    AWK_CLIENT_FUNCTION_CALL_ERROR = "AWK_CLIENT_FUNCTION_CALL_ERROR"

    AWK_CLIENT_FUNCTION_RETURN = "AWK_CLIENT_FUNTION_RETURN"
    AWK_CLIENT_FUNCTION_RETURN_ERROR = "AWK_CLIENT_FUNCTION_RETURN_ERROR"

    SERVER_REQ_CLIENT_TELEMETRY="SERVER_REQ_CLIENT_TELEMETRY"
    SERVER_REQ_CLIENT_SHUTDOWN="SERVER_REQ_CLIENT_SHUTDOWN"

    REQ_VERIFY = "REQ_VERIFY"
    REQ_FUNCTION_CALL = "REQ_FUNCTION_CALL"
    REQ_FUNCTION_RETURN = "REQ_FUNCTION_RETURN"
    REQ_GOING_SHUTDOWN = "REQ_GOING_SHUTDOWN"




class ResponsePayload:
    @staticmethod
    def client_verify_event_awk(event:str,client_id:str):
        if event == Events.AWK_CLIENT_VERIFY:
            logger.info(f"NEW: new client({client_id}) is verifyed and added in the server")
            return {"event":Events.AWK_CLIENT_VERIFY,"message":f"client({client_id}) is successfully verify"}
        elif event in [Events.AWK_CLIENT_NOT_VERIFY_DUE_TO_LIMIT,Events.AWK_CLIENT_NOT_VERIFY_DUE_TO_CHECK]:
            logger.info(f"ERROR: client({client_id}) is not added due to error")
            return {"event":Events.AWK_CLIENT_VERIFY,"message":f"client({client_id}) is not verify due to connection limit or due to client id check docs for more imformation"}
    @staticmethod
    def client_function_call_awk(event:str,sender_id:str,recever_id:str,task_id:str,function_name:str):
        if event == Events.AWK_CLIENT_FUNCTION_CALL:
            return {"event":event,"message":f"client({sender_id}) call function({function_name}) from this client({recever_id}) with task id: {task_id}"}
        elif event == Events.AWK_CLIENT_FUNCTION_CALL_ERROR:
            return {"event":event,"message":f"client({sender_id}) call function({function_name}) from this client({recever_id}) with task id: {task_id}"}
    @staticmethod
    def cleint_function_return_awk(event:str,sender_id:str,recever_id:str,task_id:str,function_name:str):
        if event == Events.AWK_CLIENT_FUNCTION_CALL:
            return {"event":event,"message":f"client({sender_id}) return function({function_name}) from this client({recever_id}) with task id: {task_id}"}
        elif event == Events.AWK_CLIENT_FUNCTION_CALL_ERROR:
            return {"event":event,"message":f"client({sender_id}) return function({function_name}) from this client({recever_id}) with task id: {task_id}"}

class EventsClientManger:
    REQ_MAKE_CLIENT_VERIFY = "REQ_MAKE_CLIENT_VERIFY"
    AWK_MAKE_CLIENT_VERIFY_SUC = "AWK_MAKE_CLIENT_VERIFY_SUC"
    AWK_MAKE_CLIENT_VERIFY_ERR = "AWK_MAKE_CLIENT_VERIFY_ERR"

    REQ_MAKE_FUNCTION_CALL = "REQ_MAKE_FUNCTION_CALL"
    AWK_MAKE_FUNCTION_CALL_SUC = "AWK_MAKE_FUNCTION_CALL_SUC"
    AWK_MAKE_FUNCTION_CALL_ERR = "AWK_MAKE_FUNCTION_CALL_ERR"

    REQ_MAKE_FUNCTION_RET = "REQ_MAKE_FUNCTION_RET"
    AWK_MAKE_FUNCTION_RET_SUC = "AWK_MAKE_FUNCTION_RET_SUC"
    AWK_MAKE_FUNCTION_RET_ERR = "AWK_MAKE_FUNCTION_RET_ERR"


class RoutingProcessPayload:
    pass