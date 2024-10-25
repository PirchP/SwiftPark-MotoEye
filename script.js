async function fetchParkingStatus() {
    try {
        console.log('Fetching parking status...');
        let response = await fetch('http://localhost:5000/parking_status.json', {
            method: 'GET',
            mode: 'cors'
        });        
        
        if (!response.ok) {
            throw new Error(`Network response was not ok: ${response.status}`);
        }
        
        let data = await response.json();
        console.log('Parking status data:', data);
        updateParkingSlots(data);
    } catch (error) {
        console.error('Error fetching parking status:', error);
    }
}

function updateParkingSlots(data) {
    data.forEach((slot) => {
        const slotElement = document.getElementById(`slot${slot.id}`);
        if (slotElement) {
            if (slot.occupied) {
                slotElement.classList.add('occupied');
                slotElement.classList.remove('available');
                slotElement.innerHTML = `ช่อง ${slot.id} <i class="fas fa-motorcycle"></i>`;
            } else {
                slotElement.classList.remove('occupied');
                slotElement.classList.add('available');
                slotElement.innerHTML = `ช่อง ${slot.id}`;
            }
        } else {
            console.warn(`ไม่พบ element ที่มี ID: slot${slot.id}`);
        }
    });
}

function animateParkingSlots() {
    fetchParkingStatus().then(() => {
        setTimeout(animateParkingSlots, 9000);
    });
}

animateParkingSlots();
