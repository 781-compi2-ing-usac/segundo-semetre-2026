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


    document.getElementById("output").textContent =
        [
            ...data.output,
            ...data.errors
        ].join("\n");

}