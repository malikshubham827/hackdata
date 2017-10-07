Dropzone.autoDiscover = false;
var dropzone = new Dropzone('form', {
  previewTemplate: document.querySelector('#preview-template').innerHTML,
  parallelUploads: 2,
  thumbnailHeight: 120,
  thumbnailWidth: 120,
  maxFilesize: 3,
  filesizeBase: 1000,
  resizeWidth: 1280,
  sending: function(file, xhr) {
    xhr.responseType = 'arraybuffer';
    xhr.responseText = null
  },
  thumbnail: function(file, dataUrl) {
    if (file.previewElement) {
      file.previewElement.classList.remove("dz-file-preview");
      var images = file.previewElement.querySelectorAll("[data-dz-thumbnail]");
      for (var i = 0; i < images.length; i++) {
        var thumbnailElement = images[i];
        thumbnailElement.alt = file.name;
        thumbnailElement.src = dataUrl;
      }
      setTimeout(function() { file.previewElement.classList.add("dz-image-preview"); }, 1);
    }
  }

});

dropzone.on("error", function(file) {
  var alert = $('.alert-danger.hidden')
    .clone()
    .removeClass('hidden')
    .append(file.name)
  $('.results').prepend(alert);
});

dropzone.on("success", function(file) {
  var blb = new Blob([file.xhr.response], {type: 'image/png'});
  var url = window.url = (window.URL || window.webkitURL).createObjectURL(blb);
  var img = new Image();
  img.src = url;
  $('.results').prepend(img)

});