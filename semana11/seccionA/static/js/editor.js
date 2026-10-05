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
int b = 5
print(a + b)
`,
            language: "python",
            theme: "vs-dark",
            automaticLayout: true
        }
    );

});


async function compileCode(){

    const mode = document.getElementById("mode-select").value;
    const builder = document.getElementById("builder-select").value;

    const response = await fetch(
        "/compile",
        {
            method:"POST",
            headers:{
                "Content-Type":"application/json"
            },
            body: JSON.stringify({
                code: editor.getValue(),
                mode: mode,
                builder: builder
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


    const output = [
        ...data.output,
        ...formattedErrors
    ].join("\n");


    document.getElementById("output").textContent = output;
    
    const copyBtn = document.getElementById("copy-btn");
    copyBtn.disabled = !output.trim();

}


async function copyOutput(){
    const output = document.getElementById("output").textContent;
    if (!output.trim()) return;
    
    try {
        await navigator.clipboard.writeText(output);
        const btn = document.getElementById("copy-btn");
        const originalText = btn.textContent;
        btn.textContent = "✓ Copiado";
        setTimeout(() => {
            btn.textContent = originalText;
        }, 1500);
    } catch (err) {
        console.error("Error al copiar:", err);
    }
}