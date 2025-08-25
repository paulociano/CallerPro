document.addEventListener('DOMContentLoaded', () => {
    // --- ELEMENTOS DA UI ---
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    const audioFileInput = document.getElementById('audioFile');
    const textInput = document.getElementById('textInput');
    const analisarBtn = document.getElementById('analisarBtn');
    const resultArea = document.getElementById('resultArea');
    const feedbackContent = document.getElementById('feedbackContent');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const uploadLabel = document.getElementById('uploadLabel');
    const fileNameDisplay = document.getElementById('fileName');

    // !!! IMPORTANTE: SUBSTITUA PELA URL DO SEU BACKEND NA RENDER !!!
    const API_URL = 'https://coach-ia-backend.onrender.com/api/analisar';

    let activeTab = 'audio'; // Inicia com a aba de áudio

    // --- LÓGICA DAS ABAS ---
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Remove a classe 'active' de todos
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Adiciona a classe 'active' ao clicado
            button.classList.add('active');
            activeTab = button.dataset.tab;
            document.getElementById(`${activeTab}-tab`).classList.add('active');
            
            // Atualiza o estado do botão 'Analisar'
            updateAnalisarButtonState();
        });
    });

    // --- LÓGICA DOS INPUTS ---
    audioFileInput.addEventListener('change', () => {
        fileNameDisplay.textContent = audioFileInput.files.length > 0 ? audioFileInput.files[0].name : '';
        updateAnalisarButtonState();
    });

    textInput.addEventListener('input', updateAnalisarButtonState);

    function updateAnalisarButtonState() {
        if (activeTab === 'audio') {
            analisarBtn.disabled = audioFileInput.files.length === 0;
        } else { // activeTab === 'text'
            analisarBtn.disabled = textInput.value.trim() === '';
        }
    }

    // --- LÓGICA DE ARRASTAR E SOLTAR (DRAG & DROP) ---
    uploadLabel.addEventListener('dragover', (e) => { e.preventDefault(); uploadLabel.classList.add('dragging'); });
    uploadLabel.addEventListener('dragleave', () => uploadLabel.classList.remove('dragging'));
    uploadLabel.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadLabel.classList.remove('dragging');
        if (e.dataTransfer.files.length > 0) {
            audioFileInput.files = e.dataTransfer.files;
            audioFileInput.dispatchEvent(new Event('change'));
        }
    });

    // --- LÓGICA DO BOTÃO ANALISAR ---
    analisarBtn.addEventListener('click', async () => {
        let requestBody;
        let requestHeaders = {};

        // Prepara a requisição baseada na aba ativa
        if (activeTab === 'audio') {
            const formData = new FormData();
            formData.append('audio', audioFileInput.files[0]);
            requestBody = formData;
            // O header 'multipart/form-data' é adicionado automaticamente pelo browser com FormData
        } else {
            requestBody = JSON.stringify({ texto: textInput.value });
            requestHeaders['Content-Type'] = 'application/json';
        }

        // Prepara a UI para o estado de carregamento
        analisarBtn.disabled = true;
        analisarBtn.textContent = 'Analisando...';
        resultArea.style.display = 'block';
        loadingSpinner.style.display = 'block';
        feedbackContent.innerHTML = '';

        try {
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: requestHeaders,
                body: requestBody
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.erro || 'Ocorreu um erro desconhecido.');
            }
            
            let formattedFeedback = result.feedback
                .replace(/✅ \*\*PONTOS POSITIVOS:\*\*/g, '<h3>✅ Pontos Positivos</h3>')
                .replace(/💡 \*\*PONTOS CONSTRUTIVOS:\*\*/g, '<h3>💡 Pontos Construtivos</h3>')
                .replace(/\n/g, '<br>');

            feedbackContent.innerHTML = formattedFeedback;

        } catch (error) {
            feedbackContent.innerHTML = `<p style="color: #ef4444;"><strong>Erro na Análise:</strong> ${error.message}</p>`;
        } finally {
            // Restaura a UI
            loadingSpinner.style.display = 'none';
            analisarBtn.disabled = false;
            analisarBtn.textContent = 'Analisar Novamente';
        }
    });
});
