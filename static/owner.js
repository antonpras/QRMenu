function toast(msg){
  const el = document.getElementById('toast');
  if(!el) return;
  el.textContent = msg;
  el.classList.remove('hidden');
  setTimeout(()=>el.classList.add('hidden'), 2000);
}

async function uploadItemImage(itemId, input){
  if(!input.files || !input.files[0]) return;
  const file = input.files[0];

  // kirim ke /owner/api/items/{id}/upload (server akan presign & upload ke R2)
  const fd = new FormData();
  fd.append('file', file);
  const r = await fetch(`/owner/api/items/${itemId}/upload`, {method:'POST', body: fd});
  if(!r.ok){ toast('Upload gagal'); return; }
  const data = await r.json();
  // update preview cepat
  const card = input.closest('[data-id]');
  if(card){
    let img = card.querySelector('img');
    if(!img){ img = document.createElement('img'); img.className='h-28 w-full object-cover rounded-lg mt-2'; card.appendChild(img); }
    img.src = data.image_url;
  }
  toast('Gambar diperbarui');
}
