class FileUpload {

    constructor(input) {
        this.input = input
        this.max_length = 1024 * 1024 * 10;
    }

    initFileUpload() {
        document.getElementById("uploaded_files").style.display= '';
        document.getElementById("dropBox").style.display= 'none';
        this.file = this.input.files[0];
        $('.filename').text(this.file.name)
        // PDFObject.embed("/media/static/artificial_intelligence_tutorial.pdf", "#resultViewer");
    }

    //upload file
    upload_file(start, model_id) {
        document.getElementById("progressBar").style.display= '';
        document.getElementById("removeFile").style.display= 'none';
        this.file = this.input.files[0];
        var end;
        var self = this;
        var existingPath = model_id;
        var formData = new FormData();
        var nextChunk = start + this.max_length + 1;
        var currentChunk = this.file.slice(start, nextChunk);
        var uploadedChunk = start + currentChunk.size
        var query = $("#query").val()
        if (uploadedChunk >= this.file.size) {
            end = 1;
        } else {
            end = 0;
        }
        formData.append('file', currentChunk)
        formData.append('filename', this.file.name)
        $('.textbox').text("Dosya yükleniyor...")

        formData.append('end', end)
        formData.append('existingPath', existingPath);
        formData.append('nextSlice', nextChunk);
        formData.append('query', query);
        $.ajaxSetup({
            headers: {
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            }
        });
        $.ajax({
            xhr: function () {
                var xhr = new XMLHttpRequest();
                xhr.upload.addEventListener('progress', function (e) {
                    if (e.lengthComputable) {
                        if (self.file.size < self.max_length) {
                            var percent = Math.round((e.loaded / e.total) * 100);
                        } else {
                            var percent = Math.round((uploadedChunk / self.file.size) * 100);
                        }
                        $('.progress-bar').css('width', percent + '%')
                        $('.progress-bar').text(percent + '%')
                    }
                });
                return xhr;
            },

            url: '/documents/search',
            type: 'POST',
            dataType: 'json',
            cache: false,
            processData: false,
            contentType: false,
            data: formData,
            error: function (xhr) {
                console.log(xhr.statusText);
            },
            success: function (res) {
                if (nextChunk < self.file.size) {
                    // upload file in chunks
                    existingPath = res.existingPath
                    self.upload_file(nextChunk, existingPath);
                } else {
                    // upload complete
                    $('.textbox').text(res.data);
                    //console.log(res.data)
                }
            }
        });
    };
}

(function ($) {
    $('#submitSearch').on('click', (event) => {
        event.preventDefault();
        var uploader = new FileUpload(document.querySelector('#fileupload'))
        uploader.upload_file(0, null);
    });
    $('#removeFile').on('click', (event) => {
        event.preventDefault();
        document.getElementById('uploaded_files').style.display= 'none';
        document.getElementById("dropBox").style.display= '';
        document.getElementById("dropBox").style.borderColor= 'gray';
        document.getElementById("dropBox").style.color= 'gray';
        document.getElementById("fileupload").value = null;
    });
    $("#fileupload").change(function (event) {
        event.preventDefault();
        var uploader = new FileUpload(document.querySelector('#fileupload'))
        uploader.initFileUpload();
    });

    ondragenter = function(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        document.getElementById("dropBox").style.borderColor= 'black';
        document.getElementById("dropBox").style.color= 'black';
    };
    
    ondragover = function(evt) {
        evt.preventDefault();
        evt.stopPropagation();
    };
    
    ondragleave = function(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        document.getElementById("dropBox").style.borderColor= 'gray';
        document.getElementById("dropBox").style.color= 'gray';
    };
      
    ondrop = function(evt) {
        evt.preventDefault();
        evt.stopPropagation();
        $("#fileupload").prop("files",evt.originalEvent.dataTransfer.files);
        var uploader = new FileUpload(evt.originalEvent.dataTransfer);
        uploader.initFileUpload();
    };
    
    $('#dropBox')
        .on('dragover', ondragover)
        .on('dragenter', ondragenter)
        .on('dragleave', ondragleave)
        .on('drop', ondrop);
})(jQuery);


