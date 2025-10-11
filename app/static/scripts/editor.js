 const quill = new Quill('#editor', {
            modules: {
                 toolbar: [
                              ['bold', 'italic', 'underline', 'strike'], // toggled buttons
                              ['blockquote', 'code-block'],
                              ['link', 'image', 'video', 'formula'],
                              [{ 'header': 1 }, { 'header': 2 }], // custom button values
                              [{ 'list': 'ordered'}, { 'list': 'bullet' }, { 'list': 'check' }],
                              [{ 'script': 'sub'}, { 'script': 'super' }], // superscript/subscript
                              [{ 'indent': '-1'}, { 'indent': '+1' }], // outdent/indent
                              [{ 'direction': 'rtl' }], // text direction
                              [{ 'size': ['small', false, 'large', 'huge'] }], // custom dropdown
                              [{ 'header': [1, 2, 3, 4, 5, 6, false] }],
                              [{ 'color': [] }, { 'background': [] }] // dropdown with defaults from theme.
                            ],
                      },
                      placeholder: 'Compose an epic...',
                      theme: 'snow', // or 'bubble'
                    });
            quill.on('editor-change', (eventName, ...args) => {
                if (eventName === 'text-change') {
                 var html = quill.root.innerHTML;
                document.getElementById('quill-html').value = html;

                } else if (eventName === 'selection-change') {
                 // args[0] will be old range
                }
            });

        //var html = quill.root.innerHTML;
        //document.getElementById('quill-html').value = html;