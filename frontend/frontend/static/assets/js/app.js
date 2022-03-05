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
    }

    //upload file
    upload_file(start, model_id, docID) {
        document.getElementById('statusMessage').style.display= 'block';
        document.getElementById("progressBar").style.display= '';
        document.getElementById("removeFile").style.display= 'none';
        //document.getElementById("pageController").style.display= 'none !important';
        $('#pageController').attr("style", "display: none !important");
        document.getElementById("resultViewer").style.display= 'none';
        var formData = new FormData();
        if (!docID) {
            this.file = this.input.files[0];
            var end;
            var self = this;
            var existingPath = model_id;
            
            var nextChunk = start + this.max_length + 1;
            var currentChunk = this.file.slice(start, nextChunk);
            var uploadedChunk = start + currentChunk.size
            if (uploadedChunk >= this.file.size) {
                end = 1;
            } else {
                end = 0;
            }
            formData.append('file', currentChunk)
            formData.append('filename', this.file.name)
    
            formData.append('end', end)
            formData.append('existingPath', existingPath);
            formData.append('nextSlice', nextChunk);
        } else {
            formData.append('docID', docID);
        }
        var user = $("#user").text()
        formData.append('user', user);
        var query = $("#query").val()
        formData.append('query', query);
        if(!docID) {
            $('#statusMessage').text("Dosya yükleniyor...")
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
                            if(percent >= 100) {
                                $('.progress-bar').css('width', '100%')
                                $('.progress-bar').text('')
                                $('.progress-bar' ).removeClass( "bg-success" ).addClass( "bg-primary progress-bar-animated" );
                            } else {
                                $('.progress-bar').css('width', percent + '%')
                                $('.progress-bar').text(percent + '%')
                            }
                        }
                    });
                    return xhr;
                },
    
                url: 'http://localhost:8080/search',
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
                        existingPath = res.existingPath
                        self.upload_file(nextChunk, existingPath, null);
                    } else if (res.resultDocUrl){
                        $('#statusMessage').text(res.message);
                        $('#resultPageList').text(res.resultPageList);
                        document.getElementById('progressBar').style.display= 'none';
                        var resultPageList = $('#resultPageList').text()
                        var pages = resultPageList.includes(",") ? $('#resultPageList').text().split(",") : $('#resultPageList').text();
                        PDFObject.embed(res.resultDocUrl, "#resultViewer", {forceIframe: true, page: pages[0]});
                        document.getElementById('pageController').style.display= '';
                        document.getElementById('resultViewer').style.display= '';
                        $('#statusMessage').css('color', 'blue')
                        $('#resultTotalPage').text("/ " + res.resultTotalPage);
                        
                        $("#pageNumber").val(1)
                        $('#pageNumber').off('input keydown keyup mousedown mouseup select contextmenu drop');
                        $("#pageNumber").inputFilter(function(value) {
                            return /^\d*$/.test(value) && (value === "" || parseInt(value) <= parseInt(res.resultTotalPage) && (value === "" || parseInt(value) >  0));
                        });
                    } else if(res.docID) {
                        existingPath = res.existingPath
                        self.upload_file(nextChunk, existingPath,res.docID);
                        $('#statusMessage').text(res.message);
                        $('#docID').text(res.docID);
                    } else {
                        $('#statusMessage').text(res.message);
                        document.getElementById('resultViewer').style.display= 'none';
                        document.getElementById('pageController').style.display= 'none'
                        // $('#pageController').attr("style", "display: none !important");
                        document.getElementById('progressBar').style.display= 'none';
                        $('#statusMessage').css('color', 'red')
                    }
                }
            });
        } else {
            $('#statusMessage').text("İşleniyor...")
            $.ajax({   
                url: 'http://localhost:8080/search',
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
                    if (res.resultDocUrl){
                        $('#statusMessage').text(res.message);
                        $('#resultPageList').text(res.resultPageList);
                        document.getElementById('progressBar').style.display= 'none';
                        var resultPageList = $('#resultPageList').text()
                        var pages = resultPageList.includes(",") ? $('#resultPageList').text().split(",") : $('#resultPageList').text();
                        PDFObject.embed(res.resultDocUrl, "#resultViewer", {forceIframe: true, page: pages[0]});
                        document.getElementById('pageController').style.display= '';
                        document.getElementById('resultViewer').style.display= '';
                        $('#statusMessage').css('color', 'blue')
                        $('#resultTotalPage').text("/ " + res.resultTotalPage);
                        
                        $("#pageNumber").val(1)
                        $('#pageNumber').off('input keydown mousedown mouseup select contextmenu drop');
                        $("#pageNumber").inputFilter(function(value) {
                            return /^\d*$/.test(value) && (value === "" || parseInt(value) <= parseInt(res.resultTotalPage) && (value === "" || parseInt(value) >  0));
                        });
                    } else {
                        $('#statusMessage').text(res.message);
                        document.getElementById('resultViewer').style.display= 'none';
                        document.getElementById('pageController').style.display= 'none'
                        // $('#pageController').attr("style", "display: none !important");
                        document.getElementById('progressBar').style.display= 'none';
                        $('#statusMessage').css('color', 'red')
                    }
                }
            });
        }
        

        $.fn.inputFilter = function(inputFilter) {
            return this.on("input keydown keyup mousedown mouseup select contextmenu drop", function() {
              if (inputFilter(this.value)) {
                this.oldValue = this.value;
                this.oldSelectionStart = this.selectionStart;
                this.oldSelectionEnd = this.selectionEnd;
              } else if (this.hasOwnProperty("oldValue")) {
                this.value = this.oldValue;
                this.setSelectionRange(this.oldSelectionStart, this.oldSelectionEnd);
              } else {
                this.value = "";
              }
            });
        };
    };
}

(function ($) {
    $(document).ready(function(){ 
        if($('#docID').length) {
            var docID = $('#docID').text()
            if (!docID) {
                document.getElementById("dropBox").style.display= '';
            } else {
                document.getElementById("removeFile").style.display= 'none';
                document.getElementById("uploaded_files").style.display= '';
                $('.progress-bar').css('width', '100%')
                $('.progress-bar').text('')
                $('.progress-bar' ).removeClass( "bg-success" ).addClass( "bg-primary progress-bar-animated" );
            }
        }
    });

    $('#submitSearch').on('click', (event) => {
        event.preventDefault();
        $('#statusMessage').css('color', 'black')
        var uploader = new FileUpload(document.querySelector('#fileupload'))
        var docID = $('#docID').text();
        docID = docID ? docID : null
        uploader.upload_file(0, null, docID);
    });
    
    $('#pageNumber').keyup(function(event) { 
        var value = $("#pageNumber").val();
        if(value) {
            var newPageIndex = parseInt(value);
            updatePdfViewer(newPageIndex)
        }

    });

    $('#pageControllerPrevious').on('click', (event) => {
        var value = $("#pageNumber").val();
        value = !value ? 2 : value;
        var newPageIndex = parseInt(value) - 1;
        resultTotalPage = parseInt($('#resultTotalPage').text().substring(2));
        newPageIndex = newPageIndex < 1 ? resultTotalPage : newPageIndex;
        updatePdfViewer(newPageIndex)
    });
    
    $('#pageControllerNext').on('click', (event) => {
        var value = $("#pageNumber").val();
        value = !value ? 0 : value;
        var newPageIndex = parseInt(value) + 1;
        resultTotalPage = parseInt($('#resultTotalPage').text().substring(2));
        newPageIndex = newPageIndex > resultTotalPage ? 1 : newPageIndex;
        updatePdfViewer(newPageIndex)
    });
    
    function updatePdfViewer(pageIndex) {
        $("#pageNumber").val(pageIndex)
        var resultPageList = $('#resultPageList').text()
        var pages =  resultPageList.includes(",") ? $('#resultPageList').text().split(",") : $('#resultPageList').text();
        var pdfviewer = document.getElementById('resultViewer');//get the viewer element
        var contenttag =  pdfviewer.getElementsByTagName("iframe")[0]//got this from pdfobject code
        var fileUrl = $(contenttag,this).attr('src').split('#')[0];
        PDFObject.embed(fileUrl, "#resultViewer", {forceIframe: true, page: pages[pageIndex-1]});   
    }

    $('#resetSearch').on('click', (event) => {
        event.preventDefault();
        var newSearch = $('#newSearch').text();
        if (!newSearch) {
            document.getElementById('uploaded_files').style.display= 'none';
            document.getElementById('resultViewer').style.display= 'none';
            document.getElementById('pageController').style.display= 'none'
            // $('#pageController').attr("style", "display: none !important");
            document.getElementById('statusMessage').style.display= 'none';
            document.getElementById('progressBar').style.display= 'none';
            document.getElementById("dropBox").style.display= '';
            document.getElementById("dropBox").style.borderColor= 'gray';
            document.getElementById("dropBox").style.color= 'gray';
            document.getElementById("fileupload").value = null;
            $('#statusMessage').css('color', 'black')
            $('#docID').text('');
            $("#query").val('');
            $('.progress-bar').css('width','0')
            $('.progress-bar' ).removeClass( "bg-primary progress-bar-animated" ).addClass( "bg-success" );
        } else {
            document.getElementById('statusMessage').style.display= 'none';
            document.getElementById('resultViewer').style.display= 'none';
            document.getElementById('progressBar').style.display= 'none';
            document.getElementById('pageController').style.display= 'none';
            // $('#pageController').attr("style", "display: none !important");
            $('#statusMessage').css('color', 'black')  
            $("#query").val('');
        }
       
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


