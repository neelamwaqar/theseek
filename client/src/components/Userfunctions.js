import axios from "axios";

export const register = (newUser) => {
  return axios
    .post("http://localhost:5000/users/register", {
      first_name: newUser.first_name,
      last_name: newUser.last_name,
      email: newUser.email,
      password: newUser.password,
    })
    .then((response) => {
      if (response.data.result) {
        return response.data.result.email;
      }
      return response.data.error;
    });
};

export const login = (user) => {
  return axios
    .post("http://localhost:5000/users/login", {
      email: user.email,
      password: user.password,
    })
    .then((response) => {
      if (response.data.token) {
        localStorage.setItem("usertoken", response.data.token);
        localStorage.setItem("useremail", response.data.email);
        localStorage.setItem("loggedIn", true);
        return response.data.token;
      }
      return response.data.error;
    })
    .catch((err) => {
      console.log(err);
      return err;
    });
};
