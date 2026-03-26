// 1. نظام الدخول السري للأدمن (200915)
async function askAdminCode() {
    const { value: code } = await Swal.fire({
        title: 'منطقة الإدارة',
        input: 'password',
        inputPlaceholder: 'أدخل الكود السري',
        background: '#1e293b',
        color: '#fff',
        confirmButtonColor: '#3b82f6',
        showCancelButton: true,
        cancelButtonText: 'إلغاء'
    });

    if (code) {
        let res = await fetch('/api/admin-login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({code: code})
        });
        
        if (res.ok) {
            Swal.fire({icon: 'success', title: 'تم الدخول', background: '#1e293b', color: '#fff', timer: 1500, showConfirmButton:false});
            document.getElementById('bot-login-section').style.display = 'block';
        } else {
            Swal.fire({icon: 'error', title: 'كود خاطئ!', background: '#1e293b', color: '#fff'});
        }
    }
}

// 2. تسجيل دخول البوت بالتوكن
async function loginBot() {
    let token = document.getElementById('bot_token').value;
    if(!token) return Swal.fire({icon:'warning', title:'أدخل التوكن أولاً'});

    let res = await fetch('/api/bot-login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({token: token})
    });
    let data = await res.json();
    
    if(data.success) {
        window.location.href = '/dashboard';
    } else {
        Swal.fire({icon:'error', title:'خطأ', text: data.message});
    }
}

// 3. تحديث بيانات البوت (الاسم والوصف)
async function updateBot(type) {
    let val = type === 'name' ? document.getElementById('bot_name').value : document.getElementById('bot_desc').value;
    if(!val) return;

    let payload = {};
    payload[type] = val;

    await fetch('/api/update-bot', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    });
    Swal.fire({icon: 'success', title: 'تم التحديث بنجاح بنجاح', background: '#1e293b', color: '#fff', timer:1500});
}

// 4. إيقاف البوت
async function stopBot() {
    let confirm = await Swal.fire({
        title: 'هل أنت متأكد؟',
        text: "سيتم حذف التوكن وتسجيل الخروج",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#d33',
        background: '#1e293b', color: '#fff'
    });

    if (confirm.isConfirmed) {
        await fetch('/api/stop-bot', {method: 'POST'});
        window.location.href = '/logout';
    }
}

// 5. نظام الإذاعة مع الـ Progress Bar
let pollInterval;
async function sendBroadcast() {
    let text = document.getElementById('broadcast_msg').value;
    if(!text) return;

    document.getElementById('btn-broadcast').disabled = true;
    document.getElementById('progress-container').classList.remove('hidden');

    let res = await fetch('/api/broadcast', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: text})
    });
    
    if(res.ok) {
        pollInterval = setInterval(checkBroadcastStatus, 1000);
    }
}

async function checkBroadcastStatus() {
    let res = await fetch('/api/broadcast/status');
    let data = await res.json();

    let percent = data.total === 0 ? 0 : Math.round((data.sent + data.failed) / data.total * 100);
    
    document.getElementById('prog-bar').style.width = `${percent}%`;
    document.getElementById('prog-percent').innerText = `${percent}%`;
    document.getElementById('prog-text').innerText = `تم إرسال: ${data.sent} | فشل: ${data.failed}`;

    if (data.status === 'finished') {
        clearInterval(pollInterval);
        document.getElementById('btn-broadcast').disabled = false;
        Swal.fire({icon: 'success', title: 'اكتملت الإذاعة', background: '#1e293b', color: '#fff'});
    }
}
