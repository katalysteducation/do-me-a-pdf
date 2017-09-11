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

/**
 * Create a job.
 */
async function create_job() {
  let html_form = $('form')
  let progress = $('.progress')
  let bar = $('.md.progress')
  let fill = $('.md.progress>div')
  let csrf_token = $('[name=csrfmiddlewaretoken]').value

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

  function show_error(err) {
    let msg = $('.progress>.error-message')
    msg.innerHTML = err
    msg.classList.remove('hidden')
    bar.classList.add('error')
    console.log(err)
  }

  // Step -1: Validate the form

  let valid = true
  for (let input of html_form) {
    if (!input.checkValidity()) {
      valid = false

      let msg = document.createElement('span')
      msg.innerText = input.validationMessage
      msg.classList.add('md', 'text-caption', 'validation-message')
      input.parentElement.insertBefore(msg, input.nextSibling)
    }
  }

  if (!valid) {
    return
  }

  document.body.classList.add('upload-started')

  // Step 0: Create a new job

  let form = new FormData(html_form)
  let rst = await fetch('/job/new/', {
    method: 'POST',
    credentials: 'same-origin',
    body: form,
  })

  if (rst.status !== 201) {
    return show_error(await rst.text())
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
    xhr.onreadystatechange = ev => {
      console.log(xhr.readyState, xhr.status)
      if (xhr.readyState !== 4) {
        return
      }
      if (xhr.status === 201) {
        return resolve()
      }
      console.log(xhr)
      show_error(Object.entries(JSON.parse(xhr.responseText)).map(([field, messages]) =>
        `<dt>${field}</dt><dd><ul>${
          messages.map(({ message }) => `<li>${ message }</li>`).join('')
        }</ul></dd>`).join(''))
      reject()
    }
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
    return show_error(await rst.text())
  }
  window.location = location
}

// If it's the new job form then register submit event
let submit = $('#submit')
console.log('submit:', submit)
if (submit) { submit.addEventListener('click', create_job) }
