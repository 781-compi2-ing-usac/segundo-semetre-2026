let editor;


require.config({
    paths: {
        vs:
        "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.52.0/min/vs"
    }
});


require(
["vs/editor/editor.main"],
function(){

    editor = monaco.editor.create(
        document.getElementById("editor"),
        {
            value:
`int a = 10

print(a)
`,
            language: "python",
            theme: "vs-dark",
            automaticLayout: true
        }
    );

});


async function compileCode(){

    const response = await fetch(
        "/compile",
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body: JSON.stringify({
                code: editor.getValue()
            })
        }
    );


    const data = await response.json();


    const formattedErrors = data.errors.map(err => {
        if (typeof err === "string") return err;
        let msg = `[${err.phase.toUpperCase()}]`;
        if (err.lineno) msg += ` (line ${err.lineno})`;
        if (err.node_type) msg += ` in ${err.node_type}`;
        msg += ` ${err.message}`;
        if (err.trace && err.trace.length > 0) {
            msg += `\n  Trace: ${err.trace.join(" -> ")}`;
        }
        return msg;
    });


    document.getElementById("output").textContent =
        [
            ...data.output,
            ...formattedErrors
        ].join("\n");

}