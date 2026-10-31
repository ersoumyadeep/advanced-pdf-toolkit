
$(document).ready(function () {

    let selectedOperation = "merge";

    // Select PDF operation
    $(".tool-btn").click(function () {

        $(".tool-btn").removeClass("active");

        $(this).addClass("active");

        selectedOperation = $(this).data("operation");

        $("#operation").val(selectedOperation);

        // Merge supports multiple files
        if (selectedOperation === "merge") {
            $("#pdfFiles").attr("multiple", true);
        } else {
            $("#pdfFiles").removeAttr("multiple");
        }

        // Show relevant options
        $("#splitOptions").prop(
            "hidden",
            selectedOperation !== "split"
        );

        $("#rotateOptions").prop(
            "hidden",
            selectedOperation !== "rotate"
        );

        // Update file list
        $("#pdfFiles").val("");
        $("#fileList").empty();
        $("#result").empty();

        // Split requires page range
        $("input[name='page_range']").prop(
            "required",
            selectedOperation === "split"
        );
    });


    // Display selected files
    $("#pdfFiles").change(function () {

        let files = this.files;

        let html = "";

        for (let i = 0; i < files.length; i++) {

            html += `
                <div class="file-name">
                    📄 ${$("<div>").text(files[i].name).html()}
                    (${(files[i].size / 1024).toFixed(2)} KB)
                </div>
            `;
        }

        $("#fileList").html(html);
    });


    // AJAX PDF processing
    $("#pdfForm").submit(function (e) {

        e.preventDefault();

        let files = $("#pdfFiles")[0].files;

        if (files.length === 0) {
            alert("Please select PDF files.");
            return;
        }

        if (selectedOperation === "merge" && files.length < 2) {
            alert("Select at least 2 PDF files.");
            return;
        }

        if (selectedOperation !== "merge" && files.length !== 1) {
            alert("Select exactly 1 PDF file.");
            return;
        }

        for (let file of files) {

            if (!file.name.toLowerCase().endsWith(".pdf")) {
                alert("Only PDF files are allowed.");
                return;
            }

            if (file.size > 10 * 1024 * 1024) {
                alert("Each file must be below 10 MB.");
                return;
            }
        }

        let formData = new FormData(this);

        $("#processBtn").prop("disabled", true)
            .text("Processing...");

        $("#progressBox").prop("hidden", false);

        $("#progressBar").css("width", "0%")
            .text("Uploading...");

        $("#result").empty();

        $.ajax({

            url: "/process/",

            type: "POST",

            data: formData,

            processData: false,

            contentType: false,

            xhr: function () {

                let xhr = new window.XMLHttpRequest();

                xhr.upload.addEventListener("progress", function (e) {

                    if (e.lengthComputable) {

                        let percent = Math.round(
                            (e.loaded / e.total) * 100
                        );

                        $("#progressBar")
                            .css("width", percent + "%")
                            .text("Uploading " + percent + "%");
                    }

                });

                return xhr;
            },

            success: function (response) {

                $("#progressBar")
                    .removeClass("progress-bar-striped progress-bar-animated")
                    .addClass("bg-success")
                    .css("width", "100%")
                    .text("Completed");

                $("#result").html(`
                    <div class="alert alert-success">
                        <h5>PDF processed successfully!</h5>

                        <p>${response.message}</p>

                        <p>File size: ${
                            (response.size / 1024).toFixed(2)
                        } KB</p>

                        <a href="${response.download_url}"
                           class="btn btn-success"
                           download>
                            Download PDF
                        </a>
                    </div>
                `);

            },

            error: function (xhr) {

                let message = "Something went wrong.";

                if (xhr.responseJSON && xhr.responseJSON.error) {
                    message = xhr.responseJSON.error;
                }

                $("#result").html(`
                    <div class="alert alert-danger">
                        ${$("<div>").text(message).html()}
                    </div>
                `);

                $("#progressBox").prop("hidden", true);
            },

            complete: function () {

                $("#processBtn")
                    .prop("disabled", false)
                    .text("Process PDF");

            }

        });

    });

});
