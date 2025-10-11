document.querySelector("form").addEventListener("submit", function (e) {
    const email = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const confirm = document.getElementById("confirm").value;
    const terms = document.querySelector("input[name='terms']").checked;

    const emailRegex = /^[\w\.-]+@[\w\.-]+\.\w+$/;
    const passwordRegex = /^(?=.*\d).{8,}$/;

    let error = "";

    if (!emailRegex.test(email)) {
      error = "Please enter a valid email address.";
    } else if (!passwordRegex.test(password)) {
      error = "Password must be at least 8 characters and include a number.";
    } else if (password !== confirm) {
      error = "Passwords do not match.";
    } else if (!terms) {
      error = "You must agree to the Terms and Services.";
    }

    if (error) {
      e.preventDefault();
      alert(error);
    }
  });