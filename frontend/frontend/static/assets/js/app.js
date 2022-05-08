class FileUpload {

    constructor(input) {
        this.input = input
        this.max_length = 1024 * 1024 * 10;
    }

    initFileUpload() {
        document.getElementById("uploaded_files").style.display= '';
        document.getElementById("dropBox").style.display= 'none';
        this.file = this.input.files[0];
        if (this.file.name.length > 35) {
            $('.filenameText').text(this.file.name.substring(0,35)+"...")
        } else {
            $('.filenameText').text(this.file.name)
        }
        $('.filename').text(this.file.name)
    }

    //upload file
    upload_file(start, model_id, docID) {
        var message = ""
        var query = $("#query").val()
        var advancedSearch = $("#advancedSearch").is(':checked') ? true : false;
        if (this.input.files[0]) {
            if (!this.input.files[0]['type'].includes("pdf")) {
                message = "Dosya Pdf Tipinde Değil. Pdf Tipinde Dosya Yükleyiniz"
            }
        }
        if (!docID && !this.input.files[0]) {    
            message = "Doküman Seçiniz"
        } else if (!query) {
            if (!advancedSearch) {
                message = "Aranılacak Nesneyi Giriniz"
            } else {
                message = "Sorgu Cümlesi Giriniz"
            }
        }

        if (message != "") {
            $('#alert_placeholder').append( $('#alert_placeholder').append(
                '<div id="alertdiv" class="container">' +
                    '<div class="alert alert-danger alert-dismissible alert-fixed" id="danger-alert" role="alert">' +
                    '<span>' + message + '</span>' + 
                    '<button type="button" class="close" data-dismiss="alert">'+
                    '<span aria-hidden="true">&times;</span>'+
                    '</button>'+
                '</div>' )
              );
          
              // close it in 3 secs
              setTimeout( function() {
                $("#alertdiv").remove();
              }, 1500 );
            return
        }
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
        formData.append('query', query);
        formData.append('advancedSearch', advancedSearch);
        
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
                        var bodyRef = document.getElementById('resultReportTable').getElementsByTagName('tbody')[0];
                        if (bodyRef)
                            bodyRef.remove()
                        var resultReport = JSON.parse(res.resultReport);
                        var columns = addAllColumnHeaders(resultReport, selector);
                        var selector = '#resultReportTable'
                        var tableBody$ = $('<tbody/>');
                        for (var i = 0; i < resultReport.length; i++) {
                          var row$ = $('<tr/>');
                          for (var colIndex = 0; colIndex < columns.length; colIndex++) {
                            var cellValue = resultReport[i][columns[colIndex]];
                            if (cellValue == null) cellValue = "";
                            if (colIndex == 1) {
                                cellValue = '<div style="width: 25px; height: 25px; background: '+ cellValue+'"></div>'
                            } 
                            row$.append($('<td/>').html(cellValue));
                          }
                          $(tableBody$).append(row$);
                        }
                        $(selector).append(tableBody$);
                        
                        $('#statusMessage').text(res.message);
                        $('#resultPageList').text(res.resultPageList);
                        document.getElementById('progressBar').style.display= 'none';
                        var resultPageList = $('#resultPageList').text()
                        var pages = resultPageList.includes(",") ? $('#resultPageList').text().split(",") : $('#resultPageList').text();
                        var firstResultPage = 0
                        if (Array.isArray(pages)) {
                            firstResultPage = pages[0]
                        } else {
                            firstResultPage = pages
                        }
                        PDFObject.embed(res.resultDocUrl, "#resultViewer", {forceIframe: true, page: firstResultPage});
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
                        if (res.resultReport) {
                            var bodyRef = document.getElementById('resultReportTable').getElementsByTagName('tbody')[0];
                            if (bodyRef)
                                bodyRef.remove()
                            var resultReport = JSON.parse(res.resultReport);
                            var columns = addAllColumnHeaders(resultReport, selector);
                            var selector = '#resultReportTable'
                            var tableBody$ = $('<tbody/>');
                            for (var i = 0; i < resultReport.length; i++) {
                              var row$ = $('<tr/>');
                              for (var colIndex = 0; colIndex < columns.length; colIndex++) {
                                var cellValue = resultReport[i][columns[colIndex]];
                                if (cellValue == null) cellValue = "";
                                if (colIndex == 1) {
                                    cellValue = '<div style="width: 25px; height: 25px; background: '+ cellValue+'"></div>'
                                } 
                                row$.append($('<td/>').html(cellValue));
                              }
                              $(tableBody$).append(row$);
                            }
                            $(selector).append(tableBody$);
                            document.getElementById('resultDetail').style.display= '';

                        }
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
                        var bodyRef = document.getElementById('resultReportTable').getElementsByTagName('tbody')[0];
                        if (bodyRef)
                            bodyRef.remove()
                        var resultReport = JSON.parse(res.resultReport);
                        var columns = addAllColumnHeaders(resultReport, selector);
                        var selector = '#resultReportTable'
                        var tableBody$ = $('<tbody/>');
                        for (var i = 0; i < resultReport.length; i++) {
                          var row$ = $('<tr/>');
                          for (var colIndex = 0; colIndex < columns.length; colIndex++) {
                            var cellValue = resultReport[i][columns[colIndex]];
                            if (cellValue == null) cellValue = "";
                            if (colIndex == 1) {
                                cellValue = '<div style="width: 25px; height: 25px; background: '+ cellValue+'"></div>'
                            } 
                            row$.append($('<td/>').html(cellValue));                 
                          }
                          $(tableBody$).append(row$);
                        }
                        $(selector).append(tableBody$);


                        $('#statusMessage').text(res.message);
                        $('#resultPageList').text(res.resultPageList);
                        document.getElementById('progressBar').style.display= 'none';
                        var resultPageList = $('#resultPageList').text()
                        var pages = resultPageList.includes(",") ? $('#resultPageList').text().split(",") : $('#resultPageList').text();
                        var firstResultPage = 0
                        if (Array.isArray(pages)) {
                            firstResultPage = pages[0]
                        } else {
                            firstResultPage = pages
                        }
                        PDFObject.embed(res.resultDocUrl, "#resultViewer", {forceIframe: true, page: firstResultPage});
                        document.getElementById('pageController').style.display= '';
                        document.getElementById('resultViewer').style.display= '';
                        document.getElementById('resultDetail').style.display= '';
                        $('#statusMessage').css('color', 'blue')
                        $('#resultTotalPage').text("/ " + res.resultTotalPage);
                        
                        $("#pageNumber").val(1)
                        $('#pageNumber').off('input keydown mousedown mouseup select contextmenu drop');
                        $("#pageNumber").inputFilter(function(value) {
                            return /^\d*$/.test(value) && (value === "" || parseInt(value) <= parseInt(res.resultTotalPage) && (value === "" || parseInt(value) >  0));
                        });
                    } else {
                        if (res.resultReport) {
                            var bodyRef = document.getElementById('resultReportTable').getElementsByTagName('tbody')[0];
                            if (bodyRef)
                                bodyRef.remove()
                            var resultReport = JSON.parse(res.resultReport);
                            var columns = addAllColumnHeaders(resultReport, selector);
                            var selector = '#resultReportTable'
                            var tableBody$ = $('<tbody/>');
                            for (var i = 0; i < resultReport.length; i++) {
                              var row$ = $('<tr/>');
                              for (var colIndex = 0; colIndex < columns.length; colIndex++) {
                                var cellValue = resultReport[i][columns[colIndex]];
                                if (cellValue == null) cellValue = "";
                                if (colIndex == 1) {
                                    cellValue = '<div style="width: 25px; height: 25px; background: '+ cellValue+'"></div>'
                                } 
                                row$.append($('<td/>').html(cellValue));
                              }
                              $(tableBody$).append(row$);
                            }
                            $(selector).append(tableBody$);
                            document.getElementById('resultDetail').style.display= '';

                        }
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
        function addAllColumnHeaders(myList, selector) {
            var columnSet = [];
            var headerTr$ = $('<tr/>');
          
            for (var i = 0; i < myList.length; i++) {
              var rowHash = myList[i];
              for (var key in rowHash) {
                if ($.inArray(key, columnSet) == -1) {
                  columnSet.push(key);
                  headerTr$.append($('<th/>').html(key));
                }
              }
            }
            $(selector).append(headerTr$);
          
            return columnSet;
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
            document.getElementById('resultDetailModal').style.display= 'none';
            document.getElementById('progressBar').style.display= 'none';
            document.getElementById('resultDetail').style.display= 'none';
            document.getElementById("dropBox").style.display= '';
            document.getElementById("dropBox").style.borderColor= 'gray';
            document.getElementById("dropBox").style.color= 'gray';
            document.getElementById("removeFile").style.display= '';
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
            document.getElementById('resultDetailModal').style.display= 'none';
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


