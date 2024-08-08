const net = require('net');
const { v4: uuidv4 } = require('uuid');

class PyGlobalInterface_Client {
    constructor(client_name) {
        this.port = 9800;
        this.host = '127.0.0.1';
        this.connection_status = false;
        this.client_name = client_name;

        this.sending_queue = [];
        this.receiving_queue = [];
        this.function_call_queue = [];
        this.function_register_hashmap = {};
        this.function_called_task_hashmap = {};
        this.rm_cli = false;

        this.connect()
            .then(() => {
                this.client_register();
                this.sender();
                this.receiver();
                this.function_processing();
            });
    }

    async connect() {
        return new Promise((resolve, reject) => {
            this.client = net.createConnection({ host: this.host, port: this.port }, () => {
                this.connection_status = true;
                resolve();
            });

            this.client.on('error', (err) => {
                this.connection_status = false;
                reject(err);
            });
        });
    }

    sender() {
        setInterval(() => {
            if (this.sending_queue.length > 0) {
                const data = this.sending_queue.shift();
                console.log(`sending data: ${JSON.stringify(data)}`);
                this.client.write(JSON.stringify(data));
            }
        }, 50);
    }

    receiver() {
        this.client.on('data', (data) => {
            const parsedData = JSON.parse(data.toString());
            console.log(`receiving from ${JSON.stringify(parsedData)}`);
            if (parsedData.event === 'func-call') {
                this.function_call_queue.push(parsedData);
            } else if (parsedData.event === 'func-ret') {
                this.function_called_task_hashmap[parsedData.task_id] = parsedData.data;
            } else if (parsedData.event === 'rm-cli') {
                this.rm_cli = true;
            } else {
                this.receiving_queue.push(parsedData);
            }
        });
    }

    function_runner(data) {
        const start = Date.now();
        const output = this.function_register_hashmap[data.function_name](data.data);
        console.log(output);
        console.log(Date.now() - start);
        this.sending_queue.push({ event: 'func-ret', data: output, to_client: data.to_client, task_id: data.task_id });
    }

    function_processing() {
        setInterval(() => {
            if (this.function_call_queue.length > 0) {
                const data = this.function_call_queue.shift();
                this.function_runner(data);
            }
        }, 50);
    }

    client_register() {
        if (this.connection_status) {
            this.sending_queue.push({ event: 'reg-cli', client_id: this.client_name });
            this.receiving_queue.push((data) => {
                if (data.event === 'reg-suc') {
                    return true;
                }
                return false;
            });
        }
    }

    func_register(function_name, function_ref) {
        if (this.connection_status) {
            this.function_register_hashmap[function_name] = function_ref;
            this.sending_queue.push({ event: 'reg-func', function_name });
            this.receiving_queue.push((data) => {
                if (data.event === 'func-reg-suc') {
                    return true;
                } else if (data.event === 'func-reg-err') {
                    return false;
                }
                return false;
            });
        }
    }

    async call_function(function_name, data) {
        const [client_name, func_name] = function_name.split('@');
        const task_id = uuidv4();
        this.function_called_task_hashmap[task_id] = null;
        this.sending_queue.push({ event: 'func-call', from_client: client_name, data, task_id, function_name: func_name });

        return new Promise((resolve) => {
            const checkFunctionCall = setInterval(() => {
                if (this.function_called_task_hashmap[task_id] !== null) {
                    clearInterval(checkFunctionCall);
                    resolve(this.function_called_task_hashmap[task_id]);
                }
            }, 30);
        });
    }

    stop() {
        this.sending_queue.push({ event: 'unreg-cli', client_name: this.client_name });
        const checkRemoveClient = setInterval(() => {
            if (this.rm_cli) {
                clearInterval(checkRemoveClient);
                this.client.end();
            }
        }, 300);
    }
}



const client = new PyGlobalInterface_Client('program4');

// Register a function
client.func_register('my_function', (data) => {
    return `Received: ${data}`;
});

// Call a function
(async () => {
    const result = await client.call_function('program1@run_function1', { key: 'value' });
    console.log(result);
})();

// Stop the client
client.stop();
