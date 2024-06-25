const PyGlobalInterface_Client = require('pyglobal-interface-client');

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
