//rsa_enc.go
package main

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "crypto/rsa"
    "crypto/sha256"
    "crypto/x509"
    "encoding/pem"
    "fmt"
    "C"
)


//-----BEGIN RSA PRIVATE KEY-----
//MIICXgIBAAKBgQDuLnQAI3mDgey3VBzWnB2L39JUU4txjeVE6myuDqkM/uGlfjb9
//SjY1bIw4iA5sBBZzHi3z0h1YV8QPuxEbi4nW91IJm2gsvvZhIrCHS3l6afab4pZB
//l2+XsDulrKBxKKtD1rGxlG4LjncdabFn9gvLZad2bSysqz/qTAUStTvqJQIDAQAB
//AoGAGRzwwir7XvBOAy5tM/uV6e+Zf6anZzus1s1Y1ClbjbE6HXbnWWF/wbZGOpet
//3Zm4vD6MXc7jpTLryzTQIvVdfQbRc6+MUVeLKwZatTXtdZrhu+Jk7hx0nTPy8Jcb
//uJqFk541aEw+mMogY/xEcfbWd6IOkp+4xqjlFLBEDytgbIECQQDvH/E6nk+hgN4H
//qzzVtxxr397vWrjrIgPbJpQvBsafG7b0dA4AFjwVbFLmQcj2PprIMmPcQrooz8vp
//jy4SHEg1AkEA/v13/5M47K9vCxmb8QeD/asydfsgS5TeuNi8DoUBEmiSJwma7FXY
//fFUtxuvL7XvjwjN5B30pNEbc6Iuyt7y4MQJBAIt21su4b3sjXNueLKH85Q+phy2U
//fQtuUE9txblTu14q3N7gHRZB4ZMhFYyDy8CKrN2cPg/Fvyt0Xlp/DoCzjA0CQQDU
//y2ptGsuSmgUtWj3NM9xuwYPm+Z/F84K6+ARYiZ6PYj013sovGKUFfYAqVXVlxtIX
//qyUBnu3X9ps8ZfjLZO7BAkEAlT4R5Yl6cGhaJQYZHOde3JEMhNRcVFMO8dJDaFeo
//f9Oeos0UUothgiDktdQHxdNEwLjQf7lJJBzV+5OtwswCWA==
//-----END RSA PRIVATE KEY-----


var privateKeyData = `
-----BEGIN PRIVATE KEY-----
MIIEowIBAAKCAQEArgh+3QUMDib9oPvLdpYjC3elEYRj4Izh0zUt787bPka/YgYn
62FSrZMBXaifY6dLymnGtNOhquu4FZyxggH03LkjqIAf1XdAbD2D40KkFArTDyZc
Dxzld8ckRittFyJv2vFzJWZJPzxElopDRZBqO+KvwIFbKbhMtlp4YnsPa27efEzJ
a5n66bAP96IuJPFUtrjeGQPeseFriQeQKK7VboxnaFcQ/JHf8cNHJoj3z6AOKKfL
1onR7hzavXwp/sm+ozlruXpS/yvXGYwGM6fRcKGko9ivxQ2+B/I5OknvzDBzDLyq
rRVP/9/PtYsB7btiaBxP6cprVIzZ5yIGvzr+CwIDAQABAoIBAQCijQLZs+YfreGG
JMlU+UTAaD9AzlRvn4cqPGisrZxwXapSh4dvvhZ4U2+aKG6/qLoM1KGpsmY1fDgT
z6io0uT/6NlagFm7i8gbkZWHhm403itm4iBoaUgXiWTjOZqKWjr52D4Bt7lAnC1A
IuJUrl/bkY8xEmGw5RiZ1oTNDz5Gy9wW9kx22JI0UkFqRCaoLIAaATbVc9u9phQj
ifdJMjkYuBPY0BkqKTjdVABDB+EmqKvSGRYRoXp9k3PE27Et+aDTY8RK7zbRHSku
yLlF2g9V4jQ2j1gBL+tN7btRzIrdp8Fy3Fh2gXP3gerV23wqF5CAmxkGMRewx2pX
zvFjgOxhAoGBANdq7K/PdK2ut1KYmqyI7n4QcAs7UVfsabd7xJa3dIupf1xOF5Vh
ptL9V2a0wzhdDirxbLOmsXRaeLjQda5xo9VsvGKSkY7BvkTBZQ3aP/q9kvL+P/7B
6x0CbbIxq1MUyEt6VFuMhJc6Azlr0MLwx04Ajk0N/Q58D2zeAFb4NG6xAoGBAM7R
smPJniO8X3DskQos1T+AYoG66WuNUKbPAqZjkRdKs82PFpYDnrw2ZihFrPSarEZU
J54e02rmldhPmaBIx5WKh6BOurBj51H7Va4Rd7WCqOAshZS8FvrP8L9CkU1I3d9V
9cFd15GtuiZq0s66sW5U9nPne3xURZcHApM1IH97AoGAUygolDm+bembRRw54U6+
2hVYW02buhg+OyFhI1lQeTWGP8i5m+Xlc19u5Ov0zIZHmNY3wyYfLK5cGeQG+b9O
om3mTxsLa5No8rvBWdadihqyZnE1nQ+YxksQs5Au9dR4+YIQnIKjEInJgtoW7Znr
JjZauG4k+Pl1Lu6ILQqFmxECgYBwrSxMU1bVz1YMFsZ6TaysmQyR8zwifW4YQyYF
cq9kii1la3R5rGU500Va4YL2DKKY+lZPPioezpuKquteuOgLn9p+SwZI/VTUhGLM
n/WhLRtGbtskCklWwh0+hkzVV0KR36oxfCfq1URak85gFLSAEMfoo4/ST7NOMeKE
Quh+qwKBgHOOxmruehs0za1YvMS86RVhOxuw3bttRdideWXXkwsrGJ/lBnrgzgcK
mJikcP9LI6uyrvMUvob1y5KNtpafFLoRUn4qqTSkThpXOMWtu/WVn8X5aQVxa/M9
wEuJ/9mDq/lZG5dqQthhcDIWSFBpFZseX8T749ffjVvp4FAL6C7e
-----END PRIVATE KEY-----
`

//export encrypt_RSA_OAEP
func encrypt_RSA_OAEP(plainText *C.char) *C.char {
    // Convert input to Go type
    plain_text := C.GoString(plainText)

    // Setup for RSA Private Key
    hash := sha256.New()
    random := rand.Reader
    privateKeyBlock, _ := pem.Decode([]byte(privateKeyData))
    var pri *rsa.PrivateKey
    pri, parseErr :=x509.ParsePKCS1PrivateKey(privateKeyBlock.Bytes)
    if parseErr != nil {
        fmt.Println("Failed to load RSA private key")
    }

    encKey := []byte(plain_text)
    var cipher_text []byte

    cipher_text, encryptErr := rsa.EncryptOAEP(hash, random, &pri.PublicKey, encKey, nil)

    if encryptErr != nil {
        fmt.Println(" RSA encrypt error : ", encryptErr)
    }

    return C.CString(string(cipher_text))

}

//export decrypt_RSA_OAEP
func decrypt_RSA_OAEP(cipherText *C.char) *C.char {
    // Convert input to Go type
    cipher_text := C.GoString(cipherText)

    // Setup for RSA Private Key
    hash := sha256.New()
    random := rand.Reader
    privateKeyBlock, _ := pem.Decode([]byte(privateKeyData))
    var pri *rsa.PrivateKey
    pri, parseErr :=x509.ParsePKCS1PrivateKey(privateKeyBlock.Bytes)
    if parseErr != nil {
        fmt.Println("Failed to load RSA private key")
    }

    // Decrypt Data
    decryptedData, decryptErr := rsa.DecryptOAEP(hash, random, pri, []byte(cipher_text), nil)

    if decryptErr != nil {
        fmt.Println(" RSA Decrypt Error: ", decryptErr)
    }

    return C.CString(string(decryptedData))

}

//export encrypt_AES_CFB
func encrypt_AES_CFB(plainText *C.char, key *C.char) *C.char {
    plain_text := C.GoString(plainText)
    aes_key := C.GoString(key)
    good_key := 32
    //aes_iv := []byte("Initiate_GoDark!")
    aes_iv := make([]byte, 16)
    for {
        rand.Read(aes_iv)
        if len(aes_iv) == 16 {
            break
        }

    }

    if len(plain_text) < 16 {
        fmt.Println("Plaintext too short %i", len(plain_text))
    }

    if len(aes_key) != good_key {
        fmt.Printf("Bad AES Key! Size: %i Payload: %s\n", len(aes_key), aes_key)
    }



    aesBlockEncrypter, err := aes.NewCipher([]byte(aes_key))
    if err != nil {
        fmt.Println("Can't Encrypt!.. We go problems..")
    }

    cipher_text := make([]byte, len(plain_text))

    aesEncrypter := cipher.NewCFBEncrypter(aesBlockEncrypter, aes_iv)

    aesEncrypter.XORKeyStream(cipher_text, []byte(plain_text))

    payload := append(aes_iv[:], cipher_text[:]...)

    return C.CString(string(payload))
}

//export decrypt_AES_CFB
func decrypt_AES_CFB(ciphertext *C.char, buffSize C.int, key *C.char) *C.char {
    var err error
    cipher_text := C.GoStringN(ciphertext, buffSize)
    aes_key := C.GoString(key)
    aes_iv := []byte(cipher_text[:16])
    encrypted_msg := []byte(cipher_text[16:])

    decrypted_text := make([]byte, len(cipher_text))

    aesBlockDecrypter, err := aes.NewCipher([]byte(aes_key))
    if err != nil {
        fmt.Println("Cant Decrypt!! We got problems..")
    }

    aesDecrypter := cipher.NewCFBDecrypter(aesBlockDecrypter, aes_iv)

    aesDecrypter.XORKeyStream(decrypted_text, encrypted_msg)


    return C.CString(string(decrypted_text))

}


func main() {}