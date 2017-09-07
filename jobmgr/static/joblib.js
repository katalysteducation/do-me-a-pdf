// let source = new EventSource('/job/1/events')

// source.onmessage = ev => {
//   console.log('message:', ev)
// }

// source.onerror = ev => {
//   console.log('error:', ev)
// }

const $ = document.querySelector.bind(document)

/**
 * Format a byte size in a human-readable format
 *
 * @param {Number} bytes
 *
 * @return {String}
 */
function formatSize(bytes) {
  const SUFFIXES = [
    'bytes', 'kiB', 'MiB', 'GiB',
  ]
  if (bytes === 0) { return '0 bytes' }
  if (bytes === 1) { return '1 byte' }
  for (let i=0, mult=1 ; i<=SUFFIXES.length ; ++i, mult *= 1024) {
    if (bytes < mult) {
      mult /= 1024;
      return (bytes / mult).toFixed(1) + ' ' + SUFFIXES[i - 1];
    }
  }
  return (bytes / 1024/1024/1024/1024).toFixed(1) + ' TiB'
}

let submit = $('#submit')
if (submit) submit.addEventListener('click', async ev => {
  let html_form = $('form')
  let progress = $('.progress')
  let bar = $('.md.progress')
  let fill = $('.md.progress>div')
  let csrf_token = $('[name=csrfmiddlewaretoken]').value
  let form = new FormData(html_form)

  document.body.classList.add('upload-started')
  let _last_class = null
  function step(num, name, text=null) {
    progress.classList.remove(_last_class)
    progress.classList.add(_last_class = `step-${name}`)
    progress.children[num-1].classList.add('done')
    progress.children[num].classList.add('started')

    if (text !== null) {
      progress.children[num].innerText = text
    }
  }

  // Step 0: Create a new job

  let rst = await fetch('/job/new/', {
    method: 'POST',
    credentials: 'same-origin',
    body: form,
  })

  if (rst.status !== 201) {
    // TODO: notify of errors
    return
  }

  let location = rst.headers.get('Location')
  let title = rst.headers.get('X-Job-Name')

  // Replace current page with job view
  document.title = title

  // Step 1: Send the artifact file
  // TODO: implement other sources

  let file = $('#collection_zip').files[0]
  form = new FormData()
  form.set('content', file)
  form.set('type', 'collection.zip')

  step(1, 'upload', `Uploading ${file.name}`)

  bar.classList.remove('indeterminate')
  bar.classList.add('determinate')
  fill.style.width = '0%'

  await new Promise((resolve, reject) => {
    let size = file.size
    let transfered = 0
    let progress = $('div.progress')
    let detail = $('div.progress>span.detail')

    let xhr = new XMLHttpRequest()
    xhr.open('post', location + 'media')
    xhr.setRequestHeader('X-CSRFToken', csrf_token)
    xhr.upload.onprogress = ev => {
      fill.style.width = ev.loaded / ev.total * 100 + '%'
      detail.innerText = formatSize(ev.loaded) + ' / ' + formatSize(size)
    }
    xhr.upload.onabort = ev => reject()
    xhr.upload.onerror = ev => reject()
    xhr.upload.onload = ev => resolve()
    xhr.send(form)
  })

  // Step 2: Job is being processed on the server

  step(2, 'processing')
  bar.classList.add('indeterminate')
  bar.classList.remove('determinate')

  let headers = new Headers()
  headers.append('X-CSRFToken', csrf_token)
  r = await fetch(location + 'start', {
    method: 'POST',
    credentials: 'same-origin',
    headers: headers,
  })

  if (r.status != 202) {
    // TODO: raise problem
  }
  window.location = location
})
